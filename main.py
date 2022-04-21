from itertools import combinations
from pysat.solvers import Minisat22
import time
import numpy as np

board = [[1, 4, 0, 0, 0, 0, 0],
         [0, 0, 3, 0, 0, 2, 0],
         [5, 0, 0, 4, 0, 0, 3],
         [0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 0, 0, 0],
         [0, 0, 0, 0, 5, 0, 0],
         [1, 0, 0, 0, 0, 0, 2]]

# expected solution:
# 1 4 4 4 3 3 3
# 1 1 3 4 3 2 3
# 5 1 3 4 3 2 3
# 5 1 3 3 3 2 2
# 5 1 1 1 1 1 2
# 5 5 5 5 5 1 2
# 1 1 1 1 1 1 2

m = len(board)
n = 5  # number of unique elements
num_vars = m * m * n


def cell(row, col, num):
    return ((row - 1) * m + (col - 1)) * n + num


def decode_cell(value):
    r = int((value - 1) / (m * m))
    c = int((value - r * m * m - 1) / m)
    v = value - r * m * m - c * m
    return r + 1, c + 1, v


def encode_digit():
    cls = []
    for i in range(1, m + 1):
        for j in range(1, m + 1):
            cls.append([cell(i, j, d) for d in range(1, n + 1)])
            for d in range(1, n):
                for dp in range(d + 1, n + 1):
                    cls.append([-cell(i, j, d), -cell(i, j, dp)])
    return cls


def get_direction(i, j):
    left = (i, j - 1) if j > 1 else None
    right = (i, j + 1) if j < m else None
    up = (i - 1, j) if i > 1 else None
    down = (i + 1, j) if i < m else None
    dirs = [d for d in [up, down, left, right] if d]
    return dirs


def encode_pair(cells, value=0):
    cls = []
    # for each pair of cells in a specified region
    for i in range(len(cells) - 1):
        for j in range(i + 1, len(cells)):
            x_i = cells[i]
            x_j = cells[j]
            if value != 0:
                cls.append([-cell(x_i[0], x_i[1], value), -cell(x_j[0], x_j[1], value)])
            # each pair does not denote the same digit; a.k.a only one digit can be present in a specified region
            else:
                for d in range(1, n + 1):
                    cls.append([-cell(x_i[0], x_i[1], d), -cell(x_j[0], x_j[1], d)])
    return cls


def encode_direction():
    cls = []
    for i in range(1, m + 1):
        for j in range(1, m + 1):
            val = board[i - 1][j - 1]
            dirs = get_direction(i, j)
            # rule 1
            if val != 0:
                # add known variables
                cls.append([cell(i, j, val)])
                # ALO
                cls.append([cell(d[0], d[1], val) for d in dirs])
                # AMO
                cls += encode_pair(dirs, value=val)
            # rule 2
            else:
                for k in range(1, n + 1):
                    if len(dirs) == 2:
                        for d in dirs:
                            if board[d[0] - 1][d[1] - 1] != 0:
                                val = board[d[0] - 1][d[1] - 1]
                            else:
                                val = k
                            cls.append([cell(d[0], d[1], val)])
                    else:
                        comb_alo = combinations(dirs, (len(dirs) - 2 + 1))
                        comb_amo = combinations(dirs, 3)
                        # at least 2 nearby cells have the same value
                        for c in list(comb_alo):
                            temp = []
                            for elem in c:
                                temp.append(cell(elem[0], elem[1], k))
                            cls.append(temp)
                        # at most 2 nearby cells have the same value
                        for c in list(comb_amo):
                            temp = []
                            for elem in c:
                                temp.append(-cell(elem[0], elem[1], k))
                            cls.append(temp)

    return cls


def solve():
    clauses = encode_digit() + encode_direction()
    # clauses = encode_direction()
    unique_clauses = set(tuple(i) for i in clauses)
    clauses = [list(i) for i in unique_clauses]
    numclause = len(clauses)
    for c in clauses:
        print(c)
    print("P CNF " + str(numclause) + " (number of clauses)")
    # solve the SAT problem
    sol = Minisat22()
    for c in clauses:
        sol.add_clause(c)
    start = time.process_time()
    sol.solve()
    end = time.process_time()
    t = end - start
    result = sol.get_model()

    return t, result


def get_result(result):

    def decode(input_result):
        res = []
        for i in range(1, num_vars + 1):
            if input_result[i - 1] > 0:
                r, c, v = decode_cell(input_result[i - 1])
                res.append([r, c, v])
        return res

    result = decode(result)

    result_sudoku = np.zeros([m, m], dtype=int)

    for data in result:
        r = int(data[0])
        c = int(data[1])
        val = data[2]
        result_sudoku[r - 1][c - 1] = val

    return result_sudoku


run_time, res = solve()
print(res)
# print(get_result(res))
# encode_direction()
# for i in range(1, m + 1):
#     for j in range(1, m + 1):
#         print(get_direction(i, j))

