import tracemalloc, time
from ortools.linear_solver import pywraplp
from others.performance import PerformanceMIP

# Single Runway
# Model
def create_mip_model_single_runway(num_planes, planes_data, separation_times):
    print("=" * 60)
    print("\t\tCreating Single Runway MIP Model")
    print("=" * 60, "\n")

    solver = pywraplp.Solver.CreateSolver('SCIP')
    variables = {}

    # Decision Variables
    # x_i: landing times
    landing_times = [
        solver.NumVar(planes_data[i]["earliest_landing_time"], planes_data[i]["latest_landing_time"], f"x_{i}")
        for i in range(num_planes)
    ]
    variables["landing_time"] = landing_times

    # delta_ij: binary order variables
    landing_order = {}
    for i in range(num_planes):
        for j in range(num_planes):
            if i != j:
                landing_order[(i, j)] = solver.BoolVar(f"delta_{i}_{j}")
    variables["landing_order"] = landing_order

    # alpha_i: early deviation
    early_deviation = [
        solver.NumVar(0, max(planes_data[i]["target_landing_time"] - planes_data[i]["earliest_landing_time"], 0), f"alpha_{i}")
        for i in range(num_planes)
    ]
    variables["early_deviation"] = early_deviation

    # beta_i: late deviation
    late_deviation = [
        solver.NumVar(0, max(planes_data[i]["latest_landing_time"] - planes_data[i]["target_landing_time"], 0), f"beta_{i}")
        for i in range(num_planes)
    ]
    variables["late_deviation"] = late_deviation

    # Sets W, U, V for constraints
    W, U, V = [], [], []
    for i in range(num_planes):
        for j in range(num_planes):
            if i != j:
                E_i, L_i = planes_data[i]['earliest_landing_time'], planes_data[i]['latest_landing_time']
                E_j, L_j = planes_data[j]['earliest_landing_time'], planes_data[j]['latest_landing_time']
                S_ij = separation_times[i][j]

                if L_i < E_j and L_i + S_ij <= E_j:
                    W.append((i, j))
                elif L_i < E_j and L_i + S_ij > E_j:
                    V.append((i, j))
                elif (E_j <= E_i <= L_j) or (E_j <= L_i <= L_j) or (E_i <= E_j <= L_i) or (E_i <= L_j <= L_i):
                    U.append((i, j))

    # Constraints
    # Each pair must satisfy delta_ij + delta_ji = 1
    for i in range(num_planes):
        for j in range(i + 1, num_planes):
            solver.Add(landing_order[(i, j)] + landing_order[(j, i)] == 1)

    # W constraints: fixed order
    for i, j in W:
        solver.Add(landing_order[(i, j)] == 1)

    # V constraints: fixed order + separation time
    for i, j in V:
        solver.Add(landing_order[(i, j)] == 1)
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j])

    # U constraints: conditional separation
    for i, j in U:
        delta_ij = landing_order[(i, j)]
        delta_ji = landing_order[(j, i)]
        L_i, E_j = planes_data[i]["latest_landing_time"], planes_data[j]["earliest_landing_time"]
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j] * delta_ij - (L_i - E_j) * delta_ji)

    # Early/Late deviation constraints
    for i in range(num_planes):
        E_i, L_i, T_i = planes_data[i]["earliest_landing_time"], planes_data[i]["latest_landing_time"], planes_data[i]["target_landing_time"]
        solver.Add(early_deviation[i] >= T_i - landing_times[i])
        solver.Add(early_deviation[i] >= 0)
        solver.Add(early_deviation[i] <= T_i - E_i)

        solver.Add(late_deviation[i] >= landing_times[i] - T_i)
        solver.Add(late_deviation[i] >= 0)
        solver.Add(late_deviation[i] <= L_i - T_i)

        # Link landing time with deviations
        solver.Add(landing_times[i] == T_i - early_deviation[i] + late_deviation[i])

    # Objective Function: minimize penalties
    objective = solver.Objective()
    for i in range(num_planes):
        objective.SetCoefficient(early_deviation[i], planes_data[i]["penalty_early"])
        objective.SetCoefficient(late_deviation[i], planes_data[i]["penalty_late"])
    objective.SetMinimization()

    print("-> Decision variables:", solver.NumVariables())
    print("-> Constraints:", solver.NumConstraints())

    return solver, variables

# Solver
def solve_single_runway_mip(num_planes, planes_data, separation_times, hint=False, performance=False):
    solver, variables = create_mip_model_single_runway(num_planes, planes_data, separation_times)

    if hint:
        target_times = [planes_data[i]["target_landing_time"] for i in range(num_planes)]
        for i in range(num_planes):
            solver.SetHint(variables["landing_time"], target_times)

    print("\n" + "=" * 60)
    print("\t\t\tSolving MIP")
    print("=" * 60, "\n")

    if performance:
        tracemalloc.start()
        start_time = time.time()

    status = solver.Solve()

    if performance:
        exec_time = time.time() - start_time
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        # Convert to MB
        memory_usage = peak_mem / 10**6

    landing_time = variables["landing_time"]
    early_deviation = variables["early_deviation"]
    late_deviation = variables["late_deviation"]

    plane_ids = [str(i) for i in range(num_planes)]
    l_times = [f"{landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i]):.2f}" 
               for i in range(num_planes)]
    earliest = [f"{planes_data[i]['earliest_landing_time']:.2f}" for i in range(num_planes)]
    targets = [f"{planes_data[i]['target_landing_time']:.2f}" for i in range(num_planes)]
    latest = [f"{planes_data[i]['latest_landing_time']:.2f}" for i in range(num_planes)]

    w_plane = max(len("Plane"), max(len(pid) for pid in plane_ids))
    w_landing = max(len("Landing Time"), max(len(lt) for lt in l_times))
    w_earliest = max(len("Earliest"), max(len(e) for e in earliest))
    w_target = max(len("Target"), max(len(t) for t in targets))
    w_latest = max(len("Latest"), max(len(l) for l in latest))

    print("-> Landing times of all planes:")
    header = f"{'Plane':>{w_plane}} | {'Landing Time':>{w_landing}} | {'Earliest':>{w_earliest}} | {'Target':>{w_target}} | {'Latest':>{w_latest}}"
    print(header)
    print("-" * len(header))

    for i in range(num_planes):
        lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
        print(f"{i:>{w_plane}} | {lt:>{w_landing}.2f} | "
              f"{planes_data[i]['earliest_landing_time']:>{w_earliest}.2f} | "
              f"{planes_data[i]['target_landing_time']:>{w_target}.2f} | "
              f"{planes_data[i]['latest_landing_time']:>{w_latest}.2f}")

    # Planes that did not land on target time
    early_dev_list = [early_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(early_deviation[i]) 
                      for i in range(num_planes)]
    late_dev_list = [late_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(late_deviation[i]) 
                     for i in range(num_planes)]
    penalty_list = [early_dev_list[i]*planes_data[i]['penalty_early'] + late_dev_list[i]*planes_data[i]['penalty_late'] 
                    for i in range(num_planes)]

    plane_ids2 = [str(i) for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    l_times2 = [f"{landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i]):.2f}" 
                for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    targets2 = [f"{planes_data[i]['target_landing_time']:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    early_dev_str = [f"{early_dev_list[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    late_dev_str = [f"{late_dev_list[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    penalty_str = [f"{penalty_list[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]

    w_plane2 = max(len("Plane"), max(len(pid) for pid in plane_ids2) if plane_ids2 else 0)
    w_landing2 = max(len("Landing Time"), max(len(lt) for lt in l_times2) if l_times2 else 0)
    w_target2 = max(len("Target"), max(len(t) for t in targets2) if targets2 else 0)
    w_early = max(len("Early Dev"), max(len(ed) for ed in early_dev_str) if early_dev_str else 0)
    w_late = max(len("Late Dev"), max(len(ld) for ld in late_dev_str) if late_dev_str else 0)
    w_penalty = max(len("Penalty"), max(len(pen) for pen in penalty_str) if penalty_str else 0)

    print("\n-> Planes that did not land on the target time:")
    header2 = f"{'Plane':>{w_plane2}} | {'Landing Time':>{w_landing2}} | {'Target':>{w_target2}} | {'Early Dev':>{w_early}} | {'Late Dev':>{w_late}} | {'Penalty':>{w_penalty}}"
    print(header2)
    print("-" * len(header2))

    any_missed = False
    for i in range(num_planes):
        if early_dev_list[i] > 0 or late_dev_list[i] > 0:
            any_missed = True
            lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
            print(f"{i:>{w_plane2}} | {lt:>{w_landing2}.2f} | "
                  f"{planes_data[i]['target_landing_time']:>{w_target2}.2f} | "
                  f"{early_dev_list[i]:>{w_early}.2f} | {late_dev_list[i]:>{w_late}.2f} | "
                  f"{penalty_list[i]:>{w_penalty}.2f}")

    if not any_missed:
        print("(none)")

    # Status
    if status == pywraplp.Solver.OPTIMAL:
        print(f"\n-> Optimal Cost: {solver.Objective().Value():.2f}")
    elif status == pywraplp.Solver.FEASIBLE:
        print("\n-> No optimal solution found. Best feasible:", round(solver.ObjectiveValue(), 2))
    else:
        print("\n-> No feasible/optimal solution found. Status:", solver.StatusName(status))

    # Metrics
    if performance:
        perf = PerformanceMIP(solver)
        print("\n-> Performance Metrics:")
        print(f"   - Execution Time: {exec_time:.4f} seconds")
        print(f"   - Memory Usage: {memory_usage:.4f} MB")
        print(f"   - Number of Variables: {perf.get_num_variables()}")
        print(f"   - Number of Constraints: {perf.get_num_constraints()}")
        print(f"   - Total Penalty: {perf.get_total_penalty():.2f}")
        print(f"   - Number of Branch-and-Bound Nodes: {perf.get_num_branch_and_bound_nodes()}")

        metrics = {
            "execution_time": exec_time,
            "memory_usage_MB": memory_usage,
            "num_variables": perf.get_num_variables(),
            "num_constraints": perf.get_num_constraints(),
            "total_penalty": round(abs(perf.get_total_penalty()), 2),
            "num_branch_and_bound_nodes": perf.get_num_branch_and_bound_nodes()
        }

    return solver, variables, metrics if performance else None

# Multiples Runways
# Model
def create_mip_model_multiple_runways(num_planes, planes_data, separation_times, separation_times_between_runways, num_runways):
    print("=" * 60)
    print("\t\tCreating Multiple Runways MIP Solver")
    print("=" * 60, "\n")

    solver = pywraplp.Solver.CreateSolver('SCIP')
    variables = {}

    # Decision Variables
    landing_times = [
        solver.NumVar(planes_data[i]["earliest_landing_time"], planes_data[i]["latest_landing_time"], f"x_{i}")
        for i in range(num_planes)
    ]
    variables["landing_time"] = landing_times

    landing_order = {}
    for i in range(num_planes):
        for j in range(num_planes):
            if i != j:
                landing_order[(i, j)] = solver.BoolVar(f"delta_{i}_{j}")
    variables["landing_order"] = landing_order

    early_deviation = [
        solver.NumVar(0, max(planes_data[i]["target_landing_time"] - planes_data[i]["earliest_landing_time"], 0), f"alpha_{i}")
        for i in range(num_planes)
    ]
    variables["early_deviation"] = early_deviation

    late_deviation = [
        solver.NumVar(0, max(planes_data[i]["latest_landing_time"] - planes_data[i]["target_landing_time"], 0), f"beta_{i}")
        for i in range(num_planes)
    ]
    variables["late_deviation"] = late_deviation

    landing_runway = {}
    same_runway = {}
    for i in range(num_planes):
        for r in range(num_runways):
            landing_runway[(i, r)] = solver.BoolVar(f"y_{i}_{r}")
        for j in range(num_planes):
            if i != j:
                same_runway[(i, j)] = solver.BoolVar(f"z_{i}_{j}")
    variables["landing_runway"] = landing_runway
    variables["same_runway"] = same_runway

    # Sets U, V, W
    W, U, V = [], [], []
    for i in range(num_planes):
        for j in range(num_planes):
            if i != j:
                E_i, L_i = planes_data[i]['earliest_landing_time'], planes_data[i]['latest_landing_time']
                E_j, L_j = planes_data[j]['earliest_landing_time'], planes_data[j]['latest_landing_time']
                S_ij = separation_times[i][j]

                if L_i < E_j and L_i + S_ij <= E_j:
                    W.append((i, j))
                elif L_i < E_j and L_i + S_ij > E_j:
                    V.append((i, j))
                elif (E_j <= E_i <= L_j) or (E_j <= L_i <= L_j) or (E_i <= E_j <= L_i) or (E_i <= L_j <= L_i):
                    U.append((i, j))

    # Constraints
    for i in range(num_planes):
        for j in range(i+1, num_planes):
            solver.Add(landing_order[(i, j)] + landing_order[(j, i)] == 1)
            solver.Add(same_runway[(i,j)] == same_runway[(j,i)])
            for r in range(num_runways):
                solver.Add(same_runway[(i,j)] >= landing_runway[(i,r)] + landing_runway[(j,r)] -1)

    for i in range(num_planes):
        solver.Add(solver.Sum([landing_runway[(i, r)] for r in range(num_runways)]) == 1)

    for i,j in W:
        solver.Add(landing_order[(i, j)] == 1)

    for i,j in V:
        solver.Add(landing_order[(i,j)] == 1)
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j] * same_runway[(i,j)] +
                   separation_times_between_runways[i][j] * (1 - same_runway[(i,j)]))

    BIG_M = max(p["latest_landing_time"] for p in planes_data) + 1000
    for i, j in U:
        delta_ij = landing_order[(i, j)]
        delta_ji = landing_order[(j, i)]

        # Make sure only one of the two constraints is active
        solver.Add(
            landing_times[j] >= landing_times[i] + separation_times[i][j] * same_runway[(i,j)]
            + separation_times_between_runways[i][j] * (1 - same_runway[(i,j)]) - BIG_M * delta_ji)

        solver.Add(
            landing_times[i] >= landing_times[j] + separation_times[j][i] * same_runway[(i,j)]
            + separation_times_between_runways[j][i] * (1 - same_runway[(i,j)]) - BIG_M * delta_ij)

    for i in range(num_planes):
        E_i, L_i, T_i = planes_data[i]["earliest_landing_time"], planes_data[i]["latest_landing_time"], planes_data[i]["target_landing_time"]
        solver.Add(early_deviation[i] >= T_i - landing_times[i])
        solver.Add(early_deviation[i] >= 0)
        solver.Add(early_deviation[i] <= T_i - E_i)

        solver.Add(late_deviation[i] >= landing_times[i] - T_i)
        solver.Add(late_deviation[i] >= 0)
        solver.Add(late_deviation[i] <= L_i - T_i)

        solver.Add(landing_times[i] == T_i - early_deviation[i] + late_deviation[i])

    # Objective Function
    objective = solver.Objective()

    for i in range(num_planes):
        objective.SetCoefficient(early_deviation[i], planes_data[i]["penalty_early"])
        objective.SetCoefficient(late_deviation[i], planes_data[i]["penalty_late"])

    objective.SetMinimization()

    print("-> Decision variables:", solver.NumVariables())
    print("-> Constraints:", solver.NumConstraints())

    return solver, variables

# Solver
def solve_multiple_runways_mip(num_planes, num_runways, planes_data, separation_times, separation_times_between_runways, hint=False, performance=False):
    solver, variables = create_mip_model_multiple_runways(
        num_planes, planes_data, separation_times, separation_times_between_runways, num_runways
    )

    if hint:
        target_times = [planes_data[i]["target_landing_time"] for i in range(num_planes)]
        for i in range(num_planes):
            solver.SetHint(variables["landing_time"], target_times)

    print("\n" + "=" * 60)
    print("\t\t\tSolving MIP")
    print("=" * 60, "\n")

    if performance:
        tracemalloc.start()
        start_time = time.time()

    status = solver.Solve()

    if performance:
        exec_time = time.time() - start_time
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        # Convert to MB
        memory_usage = peak_mem / 10**6

    landing_time = variables["landing_time"]
    early_deviation = variables["early_deviation"]
    late_deviation = variables["late_deviation"]
    landing_runway = variables["landing_runway"]

    plane_ids = [str(i) for i in range(num_planes)]
    l_times = []
    earliest = []
    targets = []
    latest = []
    runways_assigned = []

    for i in range(num_planes):
        lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
        l_times.append(f"{lt:.2f}")
        earliest.append(f"{planes_data[i]['earliest_landing_time']:.2f}")
        targets.append(f"{planes_data[i]['target_landing_time']:.2f}")
        latest.append(f"{planes_data[i]['latest_landing_time']:.2f}")

        r_assigned = None
        for r in range(num_runways):
            val = landing_runway[(i, r)].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_runway[(i, r)])
            if round(val) == 1:
                r_assigned = r
                break
        runways_assigned.append(str(r_assigned))

    w_plane = max(len("Plane"), max(len(pid) for pid in plane_ids))
    w_landing = max(len("Landing Time"), max(len(lt) for lt in l_times))
    w_earliest = max(len("Earliest"), max(len(e) for e in earliest))
    w_target = max(len("Target"), max(len(t) for t in targets))
    w_latest = max(len("Latest"), max(len(l) for l in latest))
    w_runway = max(len("Runway"), max(len(r) for r in runways_assigned))

    print("-> Landing times of all planes:")
    header = f"{'Plane':>{w_plane}} | {'Landing Time':>{w_landing}} | {'Earliest':>{w_earliest}} | {'Target':>{w_target}} | {'Latest':>{w_latest}} | {'Runway':>{w_runway}}"
    print(header)
    print("-" * len(header))

    for i in range(num_planes):
        print(f"{plane_ids[i]:>{w_plane}} | {l_times[i]:>{w_landing}} | {earliest[i]:>{w_earliest}} | {targets[i]:>{w_target}} | {latest[i]:>{w_latest}} | {runways_assigned[i]:>{w_runway}}")

    # --- Planes que não atingiram target ---
    early_dev_list = [early_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(early_deviation[i]) for i in range(num_planes)]
    late_dev_list = [late_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(late_deviation[i]) for i in range(num_planes)]
    penalty_list = [early_dev_list[i]*planes_data[i]["penalty_early"] + late_dev_list[i]*planes_data[i]["penalty_late"] for i in range(num_planes)]

    plane_ids2, l_times2, targets2, early_str, late_str, penalty_str, runways2 = [], [], [], [], [], [], []

    for i in range(num_planes):
        if early_dev_list[i] > 0 or late_dev_list[i] > 0:
            plane_ids2.append(str(i))
            lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
            l_times2.append(f"{lt:.2f}")
            targets2.append(f"{planes_data[i]['target_landing_time']:.2f}")
            early_str.append(f"{early_dev_list[i]:.2f}")
            late_str.append(f"{late_dev_list[i]:.2f}")
            penalty_str.append(f"{penalty_list[i]:.2f}")
            # Runway
            r_assigned = None
            for r in range(num_runways):
                val = landing_runway[(i, r)].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_runway[(i, r)])
                if round(val) == 1:
                    r_assigned = r
                    break
            runways2.append(str(r_assigned))

    if plane_ids2:
        w_plane2 = max(len("Plane"), max(len(pid) for pid in plane_ids2))
        w_landing2 = max(len("Landing Time"), max(len(lt) for lt in l_times2))
        w_target2 = max(len("Target"), max(len(t) for t in targets2))
        w_early = max(len("Early Dev"), max(len(e) for e in early_str))
        w_late = max(len("Late Dev"), max(len(l) for l in late_str))
        w_penalty = max(len("Penalty"), max(len(p) for p in penalty_str))
        w_runway2 = max(len("Runway"), max(len(r) for r in runways2))

        print("\n-> Planes that did not land on the target time:")
        header2 = f"{'Plane':>{w_plane2}} | {'Landing Time':>{w_landing2}} | {'Target':>{w_target2}} | {'Early Dev':>{w_early}} | {'Late Dev':>{w_late}} | {'Penalty':>{w_penalty}} | {'Runway':>{w_runway2}}"
        print(header2)
        print("-" * len(header2))

        for i in range(len(plane_ids2)):
            print(f"{plane_ids2[i]:>{w_plane2}} | {l_times2[i]:>{w_landing2}} | {targets2[i]:>{w_target2}} | {early_str[i]:>{w_early}} | {late_str[i]:>{w_late}} | {penalty_str[i]:>{w_penalty}} | {runways2[i]:>{w_runway2}}")
    else:
        print("\n(none)")

    # Status
    if status == pywraplp.Solver.OPTIMAL:
        print(f"\n-> Optimal Cost: {abs(solver.Objective().Value()):.2f}")
    elif status == pywraplp.Solver.FEASIBLE:
        print("\n-> No optimal solution found. Best feasible:", round(abs(solver.ObjectiveValue()), 2))
    else:
        print("\n-> No feasible/optimal solution found. Status:", solver.StatusName(status))

    # Metrics
    if performance:
        perf = PerformanceMIP(solver)
        print("\n-> Performance Metrics:")
        print(f"   - Execution Time: {exec_time:.4f} seconds")
        print(f"   - Memory Usage: {memory_usage:.4f} MB")
        print(f"   - Number of Variables: {perf.get_num_variables()}")
        print(f"   - Number of Constraints: {perf.get_num_constraints()}")
        print(f"   - Total Penalty: {abs(perf.get_total_penalty()):.2f}")
        print(f"   - Number of Branch-and-Bound Nodes: {perf.get_num_branch_and_bound_nodes()}")
        metrics = {
            "execution_time": exec_time,
            "memory_usage_MB": memory_usage,
            "num_variables": perf.get_num_variables(),
            "num_constraints": perf.get_num_constraints(),
            "total_penalty": round(abs(perf.get_total_penalty()), 2),
            "num_branch_and_bound_nodes": perf.get_num_branch_and_bound_nodes()
        }

    return solver, variables, metrics if performance else None
