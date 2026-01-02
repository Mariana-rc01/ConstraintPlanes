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

class PerformanceCP:
    def __init__(self, solver, model, status):
        self.solver = solver
        self.model = model
        self.status = status

    def get_execution_time(self):
        return round(self.solver.WallTime(), 7)

    def get_solution_status(self):
        return self.solver.StatusName(self.status)

    def get_num_conflicts(self):
        return self.solver.NumConflicts()

    def get_num_branches(self):
        return self.solver.NumBranches()

    def get_num_booleans(self):
        return self.solver.NumBooleans()

    def get_best_objective_bound(self):
        return self.solver.BestObjectiveBound()

    def get_num_variables(self):
        return len(self.model.Proto().variables)

    def get_num_constraints(self):
        return len(self.model.Proto().constraints)

