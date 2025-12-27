from ortools.linear_solver import pywraplp

# Single Runway
# Model
def create_mip_model_single_runway(num_planes, planes_data, separation_times):
    print("=" * 60)
    print("\t\tCreating Single Runway MIP Model")
    print("=" * 60, "\n")

    solver = pywraplp.Solver.CreateSolver('SAT')
    variables = {}

    # Decision Variables
    # x_i
    landing_times = [
        solver.NumVar(planes_data[i]["earliest_landing_time"], planes_data[i]["latest_landing_time"], f"x_{i}",)
        for i in range(num_planes)
    ]
    variables["landing_time"] = landing_times

    # delta_ij
    landing_order = {}
    for i in range(num_planes):
        for j in range(num_planes):
            if i != j:
                landing_order[(i, j)] = solver.NumVar(0, 1, f"delta_{i}_{j}")
    variables["landing_order"] = landing_order

    # alpha_i
    early_deviation = [
        solver.NumVar(0, max(planes_data[i]["target_landing_time"] - planes_data[i]["earliest_landing_time"],0, ), f"alpha_{i}",)
        for i in range(num_planes)
    ]
    variables["early_deviation"] = early_deviation

    # beta_i
    late_deviation = [
        solver.NumVar(0, max(planes_data[i]["latest_landing_time"] - planes_data[i]["target_landing_time"], 0,), f"beta_{i}",)
        for i in range(num_planes)
    ]
    variables["late_deviation"] = late_deviation

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

    for i,j in W:
        solver.Add(landing_order[(i, j)] == 1)

    for i,j in V:
        solver.Add(landing_order[(i,j)] == 1)
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j])

    for i,j in U:
        delta_ij = landing_order[(i, j)]
        delta_ji = landing_order[(j, i)]
        L_i, E_j = planes_data[i]["latest_landing_time"], planes_data[j]["earliest_landing_time"]
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j] * delta_ij - (L_i - E_j) * delta_ji)

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
def solve_single_runway_mip(num_planes, planes_data, separation_times, hint=False):
    solver, variables = create_mip_model_single_runway(num_planes, planes_data, separation_times)

    if hint:
        target_times = [planes_data[i]["target_landing_time"] for i in range(num_planes)]
        for i in range(num_planes):
            solver.SetHint(variables["landing_time"], target_times)

    print("\n" + "=" * 60)
    print("\t\t\tSolving MIP")
    print("=" * 60, "\n")

    status = solver.Solve()

    landing_time = variables["landing_time"]
    early_deviation = variables["early_deviation"]
    late_deviation = variables["late_deviation"]

    # Print all landing times
    print("-> Landing times of all planes:")
    print(f"{'Plane':>5} | {'Landing Time':>12} | {'Earliest':>8} | {'Target':>6} | {'Latest':>6}")
    print("-" * 55)
    for i in range(num_planes):
        lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
        e_i = planes_data[i]["earliest_landing_time"]
        t_i = planes_data[i]["target_landing_time"]
        l_i = planes_data[i]["latest_landing_time"]
        print(f"{i:5d} | {lt:12.2f} | {e_i:8.2f} | {t_i:6.2f} | {l_i:6.2f}")

    # Print planes that did not land on target time
    print("\n-> Planes that did not land on the target time:")
    print(f"{'Plane':>5} | {'Landing Time':>12} | {'Target':>6} | {'Early Dev':>9} | {'Late Dev':>8} | {'Penalty':>8}")
    print("-" * 65)

    for i in range(num_planes):
        e_ = early_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(early_deviation[i])
        l_ = late_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(late_deviation[i])

        if e_ > 0 or l_ > 0:
            penalty = e_ * planes_data[i]["penalty_early"] + l_ * planes_data[i]["penalty_late"]
            lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
            target_t = planes_data[i]["target_landing_time"]
            print(f"{i:5d} | {lt:12.2f} | {target_t:6.2f} | {e_:9.2f} | {l_:8.2f} | {penalty:8.2f}")

    if status == pywraplp.Solver.OPTIMAL:
        print(f"\n-> Optimal Cost: {solver.Objective().Value()}")
    elif status == pywraplp.Solver.FEASIBLE:
        print("\n-> No optimal solution found. Best feasible:", round(solver.ObjectiveValue(), 2))
    else:
        print("\n-> No feasible/optimal solution found. Status:", solver.StatusName(status))

    return solver, variables

# Multiples Runways
# Model
def create_mip_model_multiple_runways(num_planes, planes_data, separation_times, separation_times_between_runways, num_runways):
    print("=" * 60)
    print("\t\tCreating Multiple Runways MIP Solver")
    print("=" * 60, "\n")

    solver = pywraplp.Solver.CreateSolver('SAT')
    variables = {}

    # Decision Variables
    # x_i
    landing_times = [
        solver.NumVar(planes_data[i]["earliest_landing_time"], planes_data[i]["latest_landing_time"], f"x_{i}",)
        for i in range(num_planes)
    ]
    variables["landing_time"] = landing_times

    # delta_ij
    landing_order = {}
    for i in range(num_planes):
        for j in range(num_planes):
            if i != j:
                landing_order[(i, j)] = solver.NumVar(0, 1, f"delta_{i}_{j}")
    variables["landing_order"] = landing_order

    # alpha_i
    early_deviation = [
        solver.NumVar(0, max(planes_data[i]["target_landing_time"] - planes_data[i]["earliest_landing_time"],0, ), f"alpha_{i}",)
        for i in range(num_planes)
    ]
    variables["early_deviation"] = early_deviation

    # beta_i
    late_deviation = [
        solver.NumVar(0, max(planes_data[i]["latest_landing_time"] - planes_data[i]["target_landing_time"], 0,), f"beta_{i}",)
        for i in range(num_planes)
    ]
    variables["late_deviation"] = late_deviation

    # z_ij, y_ir
    landing_runway = {}
    same_runway = {}
    for i in range(num_planes):
        for r in range(num_runways):
            landing_runway[(i, r)] = solver.NumVar(0, 1, f"y_{i}_{r}")
        for j in range(num_planes):
            if i != j:
                same_runway[(i, j)] = solver.NumVar(0, 1, f"z_{i}_{j}")
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
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j] * same_runway[(i,j)] + separation_times_between_runways[i][j] * (1 - same_runway[(i,j)]))

    for i,j in U:
        delta_ij = landing_order[(i, j)]
        delta_ji = landing_order[(j, i)]
        L_i, E_j = planes_data[i]["latest_landing_time"], planes_data[j]["earliest_landing_time"]
        max_separation = max(separation_times[i][j], separation_times_between_runways[i][j])
        solver.Add(landing_times[j] >= landing_times[i] + separation_times[i][j] * same_runway[(i,j)] - (L_i  + max_separation - E_j) * delta_ji)

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
def solve_multiple_runways_mip(num_planes, num_runways, planes_data, separation_times, separation_times_between_runways, hint=False):
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

    status = solver.Solve()

    landing_time = variables["landing_time"]
    early_deviation = variables["early_deviation"]
    late_deviation = variables["late_deviation"]
    landing_runway = variables["landing_runway"]

    # Landing times table
    print("-> Landing times of all planes:")
    print(f"{'Plane':>5} | {'Landing Time':>12} | {'Earliest':>8} | {'Target':>6} | {'Latest':>6} | {'Runway':>6}")
    print("-" * 65)

    for i in range(num_planes):
        lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
        e_i = planes_data[i]["earliest_landing_time"]
        t_i = planes_data[i]["target_landing_time"]
        l_i = planes_data[i]["latest_landing_time"]

        r_assigned = None
        for r in range(num_runways):
            val = landing_runway[(i, r)].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_runway[(i, r)])
            if round(val) == 1:
                r_assigned = r
                break

        print(f"{i:5d} | {lt:12.2f} | {e_i:8.2f} | {t_i:6.2f} | {l_i:6.2f} | {r_assigned:6d}")

    # Planes missing target time
    print("\n-> Planes that did not land on the target time:")
    print(f"{'Plane':>5} | {'Landing Time':>12} | {'Target':>6} | {'Early Dev':>9} | {'Late Dev':>8} | {'Penalty':>8} | {'Runway':>6}")
    print("-" * 80)

    for i in range(num_planes):
        e_ = early_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(early_deviation[i])
        l_ = late_deviation[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(late_deviation[i])
        if e_ > 0 or l_ > 0:
            penalty = e_ * planes_data[i]["penalty_early"] + l_ * planes_data[i]["penalty_late"]
            lt = landing_time[i].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_time[i])
            target_t = planes_data[i]["target_landing_time"]

            # Assigned runway
            r_assigned = None
            for r in range(num_runways):
                val = landing_runway[(i, r)].solution_value() if status == pywraplp.Solver.OPTIMAL else solver.Value(landing_runway[(i, r)])
                if round(val) == 1:
                    r_assigned = r
                    break

            print(f"{i:5d} | {lt:12.2f} | {target_t:6.2f} | {e_:9.2f} | {l_:8.2f} | {penalty:8.2f} | {r_assigned:6d}")

    # Print cost
    if status == pywraplp.Solver.OPTIMAL:
        print(f"\n-> Optimal Cost: {solver.Objective().Value():.2f}")
    elif status == pywraplp.Solver.FEASIBLE:
        print("\n-> No optimal solution found. Best feasible:", round(solver.ObjectiveValue(), 2))
    else:
        print("\n-> No feasible/optimal solution found. Status:", solver.StatusName(status))

    return solver, variables
