import os

from solver import *
from utils import parse_puzzle


puzzle_dir = 'puzzles'


def numberlink_solver_main(filename):
    with open(filename) as f:
        board, values = parse_puzzle(f, filename=filename)

    value_var, dir_vars, num_vars, clauses, reduce_time = reduce_to_sat(board, values)

    sol, _, repairs, solve_time = solve_sat(board, values, value_var, dir_vars, clauses)


if __name__ == '__main__':
    with os.scandir(puzzle_dir) as it:
        for entry in it:
            puzzle_file = puzzle_dir + '/' + str(entry.name)

            numberlink_solver_main(puzzle_file)
