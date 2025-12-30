from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp

class PerformanceMIP:
    def __init__(self, solver):
        self.solver = solver

    def get_num_variables(self):
        return self.solver.NumVariables()

    def get_num_constraints(self):
        return self.solver.NumConstraints()

    def get_total_penalty(self):
        return self.solver.Objective().Value() if self.solver.Objective() is not None else None

    def get_num_branch_and_bound_nodes(self):
        return self.solver.nodes()
