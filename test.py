from itertools import combinations
from pysat.solvers import Minisat22

# test_list = [(1, 1), (2, 2), (3, 3), (4, 4)]
# combs = combinations(test_list, 3)
#
# for c in list(combs):
#     print(c)

test_clauses = [
[149, 219, 179],
[149, 219, 189],
[149, 179, 189],
[219, 179, 189],
[-149, -219, -179],
[-149, -219, -189],
[-149, -179, -189],
[-219, -179, -189]
]

solver = Minisat22()
for c in test_clauses:
    solver.add_clause(c)
solver.solve()
res = solver.get_model()
print(res)
