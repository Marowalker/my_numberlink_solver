from utils import *
import operator
from functools import reduce
import datetime
# import pycosat
from pysat.solvers import Minisat22
import sys


def make_value_clauses(puzzle, values, value_var):
    """Generate CNF clauses entailing the N*M value SAT variables, where N
is the number of cells and M is the number of values. Each cell
encodes a single value in a one-hot fashion.
    """

    clauses = []
    num_values = len(values)
    height = len(puzzle)
    width = min([len(r.split(' ')) for r in puzzle])

    # for each cell
    for i, j, char in explode(puzzle):

        if char.isalnum():  # flow endpoint

            endpoint_value = values[char]

            # value in this cell is this one
            clauses.append([value_var(i, j, endpoint_value)])

            # value in this cell is not the other ones
            for other_value in range(num_values):
                if other_value != endpoint_value:
                    clauses.append([-value_var(i, j, other_value)])

            # gather neighbors' variables for this value
            neighbor_vars = [value_var(ni, nj, endpoint_value) for
                             _, ni, nj in valid_neighbors(width, height, i, j)]

            # one neighbor has this value
            clauses.append(neighbor_vars)

            # no two neighbors have this value
            clauses.extend(no_two(neighbor_vars))

        else:

            # one of the values in this cell is set
            clauses.append([value_var(i, j, value)
                            for value in range(num_values)])

            # no two of the values in this cell are set
            cell_value_vars = (value_var(i, j, value) for
                               value in range(num_values))

            clauses.extend(no_two(cell_value_vars))

    return clauses


def make_dir_vars(puzzle, start_var):
    """Creates the direction-type SAT variables for each cell."""

    height = len(puzzle)
    width = min([len(r.split(' ')) for r in puzzle])
    dir_vars = dict()
    num_dir_vars = 0

    for i, j, char in explode(puzzle):

        if char.isalnum():  # flow endpoint, no dir needed
            continue

        # collect bits for neighbors (TOP BOTTOM LEFT RIGHT)
        neighbor_bits = (dir_bit for (dir_bit, ni, nj)
                         in valid_neighbors(width, height, i, j))

        # OR them all together
        cell_flags = reduce(operator.or_, neighbor_bits, 0)

        # create a lookup for dir type vars in this cell
        dir_vars[i, j] = dict()

        for code in DIR_TYPES:
            # only add var if cell has correct flags (i.e. if cell has
            # TOP, BOTTOM, RIGHT, don't add LR).
            if cell_flags & code == code:
                num_dir_vars += 1
                dir_vars[i, j][code] = start_var + num_dir_vars

    return dir_vars, num_dir_vars


def make_dir_clauses(puzzle, values, value_var, dir_vars):
    """Generate clauses involving the value and direction-type SAT
variables. Each free cell must be exactly one direction, and
directions imply value matching with neighbors.
    """

    dir_clauses = []
    num_values = len(values)
    height = len(puzzle)
    width = min([len(r.split(' ')) for r in puzzle])

    # for each cell
    for i, j, char in explode(puzzle):

        if char.isalnum():  # flow endpoint, no dir needed
            continue

        cell_dir_dict = dir_vars[(i, j)]
        cell_dir_vars = cell_dir_dict.values()

        # at least one direction is set in this cell
        dir_clauses.append(cell_dir_vars)

        # no two directions are set in this cell
        dir_clauses.extend(no_two(cell_dir_vars))

        # for each value
        for value in range(num_values):

            # get value var for this cell
            value_1 = value_var(i, j, value)

            # for each neighbor
            for dir_bit, n_i, n_j in all_neighbors(i, j):

                # get value var for other cell
                value_2 = value_var(n_i, n_j, value)

                # for each direction variable in this scell
                for dir_type, dir_var in cell_dir_dict.items():

                    # if neighbor is hit by this direction type
                    if dir_type & dir_bit:
                        # this direction type implies the values are equal
                        dir_clauses.append([-dir_var, -value_1, value_2])
                        dir_clauses.append([-dir_var, value_1, -value_2])
                    elif valid_pos(width, height, n_i, n_j):
                        # neighbor is not along this direction type,
                        # so this direction type implies the values are not equal
                        dir_clauses.append([-dir_var, -value_1, -value_2])

    return dir_clauses


def reduce_to_sat(puzzle, values):
    """Reduces the given puzzle to a SAT problem specified in CNF. Returns
a list of clauses where each clause is a list of single SAT variables,
possibly negated.
    """

    height = len(puzzle)
    width = min([len(r.split(' ')) for r in puzzle])
    num_values = len(values)

    num_cells = height * width
    num_value_vars = num_values * num_cells

    def value_var(i, j, value):
        """Return the index of the SAT variable for the given value in row i,
 column j.
        """
        return (i * width + j) * num_values + value + 1

    start = datetime.datetime.now()

    value_clauses = make_value_clauses(puzzle,
                                       values,
                                       value_var)

    dir_vars, num_dir_vars = make_dir_vars(puzzle, num_value_vars)

    dir_clauses = make_dir_clauses(puzzle, values,
                                   value_var, dir_vars)

    num_vars = num_value_vars + num_dir_vars
    clauses = value_clauses + dir_clauses

    reduce_time = (datetime.datetime.now() - start).total_seconds()

    return value_var, dir_vars, num_vars, clauses, reduce_time


def decode_solution(puzzle, values, value_var, dir_vars, sol):
    """Takes the solution set from SAT and decodes it by undoing the
one-hot encoding in each cell for value and direction-type. Returns a
2D array of (value, direction-type) pairs.
    """

    sol = set(sol)
    num_values = len(values)

    decoded = []

    for i, row in enumerate(puzzle):

        decoded_row = []
        elems = row.split(' ')
        # for j, char in enumerate(row):
        for j, char in enumerate(elems):

            # find which value variable for this cell is in the
            # solution set
            cell_value = -1

            for value in range(num_values):
                if value_var(i, j, value) in sol:
                    assert cell_value == -1
                    cell_value = value

            assert cell_value != -1

            cell_dir_type = -1

            if not char.isalnum():  # not a flow endpoint

                # find which dir type variable for this cell is in the
                # solution set
                for dir_type, dir_var in dir_vars[i, j].items():
                    if dir_var in sol:
                        assert cell_dir_type == -1
                        cell_dir_type = dir_type

                assert cell_dir_type != -1

            decoded_row.append((cell_value, cell_dir_type))

        decoded.append(decoded_row)

    return decoded


def make_path(decoded, visited, cur_i, cur_j):
    """Follow a path starting from an arbitrary row, column location on
the grid until a non-path cell is detected, or a cycle is
found. Returns a list of (row, column) pairs on the path, as well as a
boolean flag indicating if a cycle was detected.
    """

    height = len(decoded)
    width = min([len(r) for r in decoded])

    run = []
    is_cycle = False
    prev_i, prev_j = -1, -1

    while True:

        advanced = False

        # get current cell, set visited, add to path
        value, dir_type = decoded[cur_i][cur_j]
        visited[cur_i][cur_j] = 1
        run.append((cur_i, cur_j))

        # loop over valid neighbors
        for dir_bit, n_i, n_j in valid_neighbors(width, height, cur_i, cur_j):

            # do not consider prev pos
            if (n_i, n_j) == (prev_i, prev_j):
                continue

            # get neighbor value & dir type
            n_value, n_dir_type = decoded[n_i][n_j]

            # these are connected if one of the two dir type variables
            # includes the (possibly flipped) direction bit.
            if ((dir_type >= 0 and (dir_type & dir_bit)) or
                    (dir_type == -1 and n_dir_type >= 0 and
                     n_dir_type & DIR_FLIP[dir_bit])):

                # if connected, they better be the same value
                assert value == n_value

                # detect cycle
                if visited[n_i][n_j]:
                    is_cycle = True
                else:
                    prev_i, prev_j = cur_i, cur_j
                    cur_i, cur_j = n_i, n_j
                    advanced = True

                # either cycle detected or path advanced, so stop
                # looking at neighbors
                break

        # if path not advanced, quit
        if not advanced:
            break

    return run, is_cycle


def detect_cycles(decoded, dir_vars):
    """Examine the decoded SAT solution to see if any cycles exist; if so,
return the CNF clauses that need to be added to the problem in order
to prevent them.
    """

    height = len(decoded)
    width = min([len(r) for r in decoded])

    values_seen = set()
    visited = [[0] * width for _ in range(height)]

    # for each cell
    for i, j, (value, dir_type) in explode(decoded):

        # if flow endpoint for value we haven't dealt with yet
        if dir_type == -1 and value not in values_seen:
            # add it to set of values dealt with
            assert not visited[i][j]
            values_seen.add(value)

            # mark the path as visited
            run, is_cycle = make_path(decoded, visited, i, j)
            assert not is_cycle

    # see if there are any unvisited cells, if so they have cycles
    extra_clauses = []

    for i, j in itertools.product(range(height), range(width)):
        if not visited[i][j]:

            # get the path
            run, is_cycle = make_path(decoded, visited, i, j)
            assert is_cycle

            # generate a clause negating the conjunction of all
            # direction types along the cycle path.
            clause = []

            for r_i, r_j in run:
                _, dir_type = decoded[r_i][r_j]
                dir_var = dir_vars[r_i, r_j][dir_type]
                clause.append(-dir_var)

            extra_clauses.append(clause)

    # return whatever clauses we had to generate
    return extra_clauses


def show_solution(values, decoded):
    """Print the puzzle solution to the terminal."""

    # make an array to flip the key/value in the values dict so we can
    # index characters numerically:

    value_chars = [None] * len(values)

    for char, value in values.items():
        value_chars[value] = char
        # do_value = do_value and ANSI_LOOKUP.has_key(char)

    for decoded_row in decoded:
        for (value, dir_type) in decoded_row:

            assert 0 <= value < len(values)

            value_char = value_chars[value]

            if dir_type == -1:
                display_char = value_char
            else:
                display_char = DIR_LOOKUP[dir_type]

            sys.stdout.write(display_char)
            sys.stdout.write(' ')

        # sys.stdout.write(ANSI_RESET)

        sys.stdout.write('\n')


def solve_sat(puzzle, values, value_var, dir_vars, clauses):
    """Solve the SAT now that it has been reduced to a list of clauses in
CNF.  This is an iterative process: first we try to solve a SAT, then
we detect cycles. If cycles are found, they are prevented from
recurring, and the next iteration begins. Returns the SAT solution
set, the decoded puzzle solution, and the number of cycle repairs
needed.
    """

    start = datetime.datetime.now()

    decoded = None
    all_decoded = []
    repairs = 0

    sol = Minisat22()
    for c in clauses:
        sol.add_clause(c)

    while True:

        # sol = pycosat.solve(clauses)  # pylint: disable=E1101
        sol.solve()
        sol = sol.get_model()

        if not isinstance(sol, list):
            decoded = None
            all_decoded.append(decoded)
            break

        decoded = decode_solution(puzzle, values, value_var, dir_vars, sol)
        all_decoded.append(decoded)

        extra_clauses = detect_cycles(decoded, dir_vars)

        if not extra_clauses:
            break

        clauses += extra_clauses
        repairs += 1

    solve_time = (datetime.datetime.now() - start).total_seconds()

    if decoded is None:
        print(
            'solver returned {} after {:,} cycle repairs and {:.3f} seconds'.format(
                str(sol), repairs, solve_time))

    else:
        print('obtained solution after {:,} cycle repairs and {:.3f} seconds:'.format(
            repairs, solve_time))
        show_solution(values, decoded)

    return sol, decoded, repairs, solve_time


with open('puzzles/extreme_25x25_60.txt', 'r') as infile:
    # puzzle, values = parse_puzzle(options, infile, filename)
    board, values = parse_puzzle(infile, filename='puzzles/extreme_25x25_60.txt')

value_var, dir_vars, num_vars, clauses, reduce_time = reduce_to_sat(board, values)

sol, _, repairs, solve_time = solve_sat(board, values, value_var, dir_vars, clauses)

# print(sol)
