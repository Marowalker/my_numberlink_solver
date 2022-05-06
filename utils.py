import itertools
from constants import *


def all_pairs(collection):
    """Return all combinations of two items from a collection, useful for
making a large number of SAT variables mutually exclusive.
    """

    return itertools.combinations(collection, 2)


def no_two(satvars):
    """Given a collection of SAT variables, generates clauses specifying
that no two of them can be true at the same time.
    """

    return ((-a, -b) for (a, b) in all_pairs(satvars))


def explode(puzzle):
    """Iterator helper function to allow looping over 2D arrays without
nested 'for' loops.
    """

    for i, row in enumerate(puzzle):
        if isinstance(row, str):
            elems = row.split(' ')
        else:
            elems = row
        for j, char in enumerate(elems):
            yield i, j, char


def valid_pos(width, height, i, j):
    """Check whether a position on a square grid is valid."""
    return 0 <= i < height and 0 <= j < width


def all_neighbors(i, j):
    """Return all neighbors of a grid square at row i, column j."""
    return ((dir_bit, i+delta_i, j+delta_j)
            for (dir_bit, delta_i, delta_j) in DELTAS)


def valid_neighbors(width, height, i, j):
    """Return all actual on-grid neighbors of a grid square at row i,
column j."""

    return ((dir_bit, ni, nj) for (dir_bit, ni, nj)
            in all_neighbors(i, j)
            if valid_pos(width, height, ni, nj))


def parse_puzzle(file_or_str, filename='input'):

    """Convert the given string or file object into a square array of
strings. Also return a dictionary which maps input characters to value
indices.
    """

    if not isinstance(file_or_str, str):
        file_or_str = file_or_str.read()

    puzzle = file_or_str.splitlines()

    # assume size based on length of first line
    width = min([len(r.split(' ')) for r in puzzle])
    height = len(puzzle)
    # size = len(puzzle[0])

    # count values and build lookup
    values = dict()
    value_count = []

    for i, row in enumerate(puzzle):
        elems = row.split(' ')
        if len(elems) != width:
            print('{}:{} row size mismatch'.format(filename, i+1))
            return None, None
        for j, char in enumerate(elems):
            if char.isalnum():  # flow endpoint
                if char in values:
                    value = values[char]
                    if value_count[value]:
                        print('{}:{}:{} too many {} already'.format(
                            filename, i+1, j, char))
                        return None, None
                    value_count[value] = 1
                else:
                    value = len(values)
                    values[char] = value
                    value_count.append(0)

    # check parity
    for char, value in values.items():
        if not value_count[value]:
            print('value {} has start but no end!'.format(char))
            return None, None

    # print info
    print('read {}x{} puzzle with {} values from {}'.format(
        width, height, len(values), filename))

    return puzzle, values
