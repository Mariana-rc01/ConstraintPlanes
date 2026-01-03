from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp
import time
import psutil

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

class PerformanceHybrid:
    def __init__(self):
        self.start_time = None
        self.end_time = None

        self.num_iterations = 0
        self.converged = False

        # CP
        self.cp_total_time = 0.0
        self.cp_num_branches = 0
        self.cp_num_conflicts = 0
        self.cp_num_booleans = 0
        self.cp_num_variables = 0
        self.cp_num_constraints = 0

        # MIP
        self.mip_total_time = 0.0
        self.mip_num_calls = 0

        # Memory
        self.memory_start = 0.0
        self.memory_end = 0.0
        self.memory_peak = 0.0

    def _get_current_memory_usage(self):
        process = psutil.Process()
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)  # Convert to MB

    def start(self):
        self.start_time = time.time()
        self.memory_start = self._get_current_memory_usage()
        self.memory_peak = self.memory_start

    def update_memory_peak(self):
        current_memory = self._get_current_memory_usage()
        self.memory_peak = max(current_memory, self.memory_peak)

    def stop(self):
        self.end_time = time.time()
        self.memory_end = self._get_current_memory_usage()

    def update_cp_metrics(self, solver, model):
        self.cp_total_time += round(solver.WallTime(), 7)
        self.cp_num_branches += solver.NumBranches()
        self.cp_num_conflicts += solver.NumConflicts()
        self.cp_num_booleans = solver.NumBooleans()
        self.cp_num_variables = len(model.Proto().variables)
        self.cp_num_constraints = len(model.Proto().constraints)
        self.update_memory_peak()

    def update_mip_metrics(self, time):
        self.mip_num_calls += 1
        self.mip_total_time += time
        self.update_memory_peak()

    def return_metrics(self, iterations, converged):
        self.num_iterations = iterations
        self.converged = converged

    def get_total_wall_time(self):
        if self.start_time is None or self.end_time is None:
            return None
        return round(self.end_time - self.start_time, 7)

    def get_peak_memory_usage(self):
        return round(self.memory_peak, 7)

    def get_memory_overhead(self):
        return round(self.memory_peak - self.memory_start, 7)