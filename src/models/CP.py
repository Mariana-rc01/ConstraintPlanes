from ortools.sat.python import cp_model
import psutil

# Single Runway
# Model
def create_cp_model_single_runway(num_planes, planes_data, separation_times):
    print("=" * 60)
    print("\t\t     Creating CP model")
    print("=" * 60, "\n")

    # Create the CP-SAT model
    model = cp_model.CpModel()

    # 1) EXTRACT RELEVANT DATA INTO ARRAYS (for convenience)
    E = [p["earliest_landing_time"] for p in planes_data]  # Earliest landing times
    T = [p["target_landing_time"]   for p in planes_data]  # Target landing times
    L = [p["latest_landing_time"]   for p in planes_data]  # Latest landing times
    cost_e = [p["penalty_early"]    for p in planes_data]  # Penalty for early_deviation
    cost_l = [p["penalty_late"]     for p in planes_data]  # Penalty for late_deviation

    # 2) VARIABLE CREATION

    # 'xi' is the time plane i actually lands
    landing_time = [
        model.NewIntVar(0, 10_000_000, f"landing_time_{i}")
        for i in range(num_planes)
    ]

    # 'alpha' measures how many time units plane i lands before target
    early_deviation = [
        model.NewIntVar(
            0,
            max(T[i] - E[i], 0),  # Max possible early_deviation
            f"early_deviation_{i}")
        for i in range(num_planes)]

    # 'beta' measures how many time units plane i lands after target
    late_deviation = [
        model.NewIntVar(
            0,
            max(L[i] - T[i], 0),  # Max possible late_deviation
            f"late_deviation_{i}")
        for i in range(num_planes)]

    # Boolean variables: before_ij = True if plane i lands before plane j (i < j).
    # We'll store these in a 2D list for convenience.
    before_ij = []
    for i in range(num_planes):
        row = []
        for j in range(num_planes):
            if j > i:
                # Only define it for j > i to avoid duplication
                row.append(model.NewBoolVar(f"before_ij_{i}_{j}"))
            else:
                # For j <= i, we can store None (or a dummy variable)
                row.append(None)
        before_ij.append(row)

    # 3) SETS U, V, W
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


    # 4) CONSTRAINTS
    for i in range(num_planes):
        # Landing time must be within [earliest, latest]
        model.Add(landing_time[i] >= E[i])
        model.Add(landing_time[i] <= L[i])

        # Define early_deviation and late_deviation
        model.Add(early_deviation[i] >= T[i] - landing_time[i])
        model.Add(late_deviation[i] >= landing_time[i] - T[i])

    for i in range(num_planes):
        for j in range(num_planes):
            if j > i:
                before_ij_var = before_ij[i][j]
                before_ji_var = before_ij_var.Not()

    for i,j in V:
        S_ij = separation_times[i][j]
        model.Add(landing_time[j] >= landing_time[i] + S_ij)

    for i,j in U:
        if i < j:
            S_ij = separation_times[i][j]
            S_ji = separation_times[j][i]
            before_ij_var = before_ij[i][j]
            model.Add(landing_time[j] >= landing_time[i] + S_ij).OnlyEnforceIf(before_ij_var)
            model.Add(landing_time[i] >= landing_time[j] + S_ji).OnlyEnforceIf(before_ij_var.Not())

    # 5) OBJECTIVE FUNCTION
    cost_terms = []
    for i in range(num_planes):
        cost_terms.append(cost_e[i] * early_deviation[i])
        cost_terms.append(cost_l[i] * late_deviation[i])

    model.Minimize(sum(cost_terms))

    # 6) RETURN MODEL AND VARIABLES
    variables = {
        "landing_time": landing_time,
        "early_deviation": early_deviation,
        "late_deviation": late_deviation,
        "before_ij": before_ij
    }

    return model, variables

# Solver
def solve_single_runway_cp(num_planes, planes_data, separation_times,
                           decision_strategies=None, hint=False,
                           search_strategy=cp_model.AUTOMATIC_SEARCH):
    """Builds and solves the single-runway CP model with a permutation approach."""
    model, vars_ = create_cp_model_single_runway(
        num_planes, planes_data, separation_times
    )

    if hint:
        for i in range(num_planes):
            model.AddHint(vars_["landing_time"][i], planes_data[i]["target_landing_time"])

    # Create solver instance
    solver = cp_model.CpSolver()
    solver.parameters.search_branching = search_strategy

    print("-> Number of decision variables created:", len(model.Proto().variables))
    print("-> Number of constraints:", len(model.Proto().constraints))
    print("\n" + "=" * 60)
    print("\t\t\tSolving CP")
    print("=" * 60, "\n")

    # Apply decision strategies if provided
    if decision_strategies:
        for strategy in decision_strategies:
            var_names = strategy["variables"]
            if isinstance(var_names, str):
                var_list = vars_.get(var_names, [])
            elif isinstance(var_names, list):
                var_list = []
                for var_name in var_names:
                    var_list.extend(vars_.get(var_name, []))
            else:
                raise ValueError("The 'variables' field must be a string or list of strings.")

            model.AddDecisionStrategy(
                var_list,
                strategy["variable_strategy"],
                strategy["value_strategy"]
            )

    # Solve
    status = solver.Solve(model)

    landing_time = vars_["landing_time"]
    early_deviation = vars_["early_deviation"]
    late_deviation = vars_["late_deviation"]

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        plane_ids = [str(i) for i in range(num_planes)]
        l_times = [f"{solver.Value(landing_time[i]):.2f}" for i in range(num_planes)]
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
            print(f"{i:>{w_plane}} | {solver.Value(landing_time[i]):>{w_landing}.2f} | "
                  f"{planes_data[i]['earliest_landing_time']:>{w_earliest}.2f} | "
                  f"{planes_data[i]['target_landing_time']:>{w_target}.2f} | "
                  f"{planes_data[i]['latest_landing_time']:>{w_latest}.2f}")

        # Planes that did not land on target time
        early_dev_list = [solver.Value(early_deviation[i]) for i in range(num_planes)]
        late_dev_list = [solver.Value(late_deviation[i]) for i in range(num_planes)]
        penalty_list = [early_dev_list[i]*planes_data[i]['penalty_early'] + late_dev_list[i]*planes_data[i]['penalty_late'] 
                        for i in range(num_planes)]

        plane_ids2 = [str(i) for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
        l_times2 = [f"{solver.Value(landing_time[i]):.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
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
                print(f"{i:>{w_plane2}} | {solver.Value(landing_time[i]):>{w_landing2}.2f} | "
                      f"{planes_data[i]['target_landing_time']:>{w_target2}.2f} | "
                      f"{early_dev_list[i]:>{w_early}.2f} | {late_dev_list[i]:>{w_late}.2f} | "
                      f"{penalty_list[i]:>{w_penalty}.2f}")

        if not any_missed:
            print("(none)")

        # Print objective / status
        if status == cp_model.OPTIMAL:
            print(f"\n-> Optimal Cost: {solver.ObjectiveValue()}")
        else:
            print("\n-> No optimal solution found. Best feasible:", round(solver.ObjectiveValue(), 2))
    else:
        print("\n-> No feasible/optimal solution found. Status:", solver.StatusName(status))

    metrics = {}
    return solver, model, vars_, metrics

# Multiples Runways
# Model
def create_cp_model_multiple_runway(num_planes, num_runways, planes_data, separation_times, separation_times_between_runways):
    print("=" * 60)
    print("\t\t     Creating CP model")
    print("=" * 60, "\n")

    # Create the CP-SAT model
    model = cp_model.CpModel()

    # 1) EXTRACT RELEVANT DATA INTO ARRAYS (for convenience)
    E = [p["earliest_landing_time"] for p in planes_data]  # Earliest landing times
    T = [p["target_landing_time"]   for p in planes_data]  # Target landing times
    L = [p["latest_landing_time"]   for p in planes_data]  # Latest landing times
    cost_e = [p["penalty_early"]    for p in planes_data]  # Penalty for early_deviation
    cost_l = [p["penalty_late"]     for p in planes_data]  # Penalty for late_deviation

    # 2) VARIABLE CREATION

    # 'xi' is the time plane i actually lands
    landing_time = [
        model.NewIntVar(0, 10_000_000, f"landing_time_{i}")
        for i in range(num_planes)
    ]

    # 'alpha' measures how many time units plane i lands before target
    early_deviation = [
        model.NewIntVar(
            0,
            max(T[i] - E[i], 0),  # Max possible early_deviation
            f"early_deviation_{i}")
        for i in range(num_planes)]

    # 'beta' measures how many time units plane i lands after target
    late_deviation = [
        model.NewIntVar(
            0,
            max(L[i] - T[i], 0),  # Max possible late_deviation
            f"late_deviation_{i}")
        for i in range(num_planes)]

    # Boolean variables: before_ij = True if plane i lands before plane j (i < j).
    # We'll store these in a 2D list for convenience.
    before_ij = []
    for i in range(num_planes):
        row = []
        for j in range(num_planes):
            if j > i:
                # Only define it for j > i to avoid duplication
                row.append(model.NewBoolVar(f"before_ij_{i}_{j}"))
            else:
                # For j <= i, we can store None (or a dummy variable)
                row.append(None)
        before_ij.append(row)

    # 'runway[i]' is the index of the runway on which plane i lands
    runway_i = [model.NewIntVar(0, num_runways - 1, f"runway_{i}") for i in range(num_planes)]

    # 3) SETS U, V, W
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


    # 4) CONSTRAINTS
    for i in range(num_planes):
        # Landing time must be within [earliest, latest]
        model.Add(landing_time[i] >= E[i])
        model.Add(landing_time[i] <= L[i])

        # Define early_deviation and late_deviation
        model.Add(early_deviation[i] >= T[i] - landing_time[i])
        model.Add(late_deviation[i] >= landing_time[i] - T[i])

    for i in range(num_planes):
        for j in range(num_planes):
            if j > i:
                before_ij_var = before_ij[i][j]
                before_ji_var = before_ij_var.Not()

    # Reified equality: same_runway[i][j] <-> (runway_i[i] == runway_i[j])
    # Only for i < j
    same_runway = [[None] * num_planes for _ in range(num_planes)]
    for i in range(num_planes):
        for j in range(i + 1, num_planes):
            b = model.NewBoolVar(f"same_runway_{i}_{j}")
            same_runway[i][j] = b

            # b => runway_i[i] == runway_i[j]
            model.Add(runway_i[i] == runway_i[j]).OnlyEnforceIf(b)
            # not b => runway_i[i] != runway_i[j]
            model.Add(runway_i[i] != runway_i[j]).OnlyEnforceIf(b.Not())

    def get_same_runway_bool(i, j):
        # returns BoolVar representing (runway_i[i] == runway_i[j])
        if i < j:
            return same_runway[i][j]
        else:
            return same_runway[j][i]

    # V constraints
    for i, j in V:
        S_ij = separation_times[i][j]
        s_ij = separation_times_between_runways[i][j]

        b_same = get_same_runway_bool(i, j)

        model.Add(landing_time[j] >= landing_time[i] + S_ij).OnlyEnforceIf(b_same)
        model.Add(landing_time[j] >= landing_time[i] + s_ij).OnlyEnforceIf(b_same.Not())

    # U constraints
    for i, j in U:
        if i < j:
            S_ij = separation_times[i][j]
            S_ji = separation_times[j][i]
            s_ij = separation_times_between_runways[i][j]
            s_ji = separation_times_between_runways[j][i]

            before_ij_var = before_ij[i][j]
            before_ji_var = before_ij_var.Not()

            b_same = get_same_runway_bool(i, j)

            # i before j
            model.Add(landing_time[j] >= landing_time[i] + S_ij).OnlyEnforceIf([before_ij_var, b_same])
            model.Add(landing_time[j] >= landing_time[i] + s_ij).OnlyEnforceIf([before_ij_var, b_same.Not()])

            # j before i
            model.Add(landing_time[i] >= landing_time[j] + S_ji).OnlyEnforceIf([before_ji_var, b_same])
            model.Add(landing_time[i] >= landing_time[j] + s_ji).OnlyEnforceIf([before_ji_var, b_same.Not()])


    # 5) OBJECTIVE FUNCTION
    cost_terms = []
    for i in range(num_planes):
        cost_terms.append(cost_e[i] * early_deviation[i])
        cost_terms.append(cost_l[i] * late_deviation[i])

    model.Minimize(sum(cost_terms))

    # 6) RETURN MODEL AND VARIABLES
    variables = {
        "landing_time": landing_time,
        "early_deviation": early_deviation,
        "late_deviation": late_deviation,
        "before_ij": before_ij,
        "runway_i": runway_i
    }

    return model, variables

# Solver
def solve_multiple_runways_cp(num_planes, num_runways, planes_data, separation_times, separation_times_between_runways, decision_strategies=None, hint=False, search_strategy=cp_model.AUTOMATIC_SEARCH):
    """Builds and solves the multiple-runway CP model with a permutation approach."""
    model, vars_ = create_cp_model_multiple_runway(
        num_planes, num_runways, planes_data, separation_times, separation_times_between_runways
    )

    if hint:
        for i in range(num_planes):
            model.AddHint(vars_["landing_time"][i], planes_data[i]["target_landing_time"])

    # Create solver instance
    solver = cp_model.CpSolver()
    solver.parameters.search_branching = search_strategy

    print("-> Number of decision variables created:", len(model.Proto().variables))
    print("-> Number of constraints:", len(model.Proto().constraints))
    print("\n" + "=" * 60)
    print("\t\t\tSolving CP")
    print("=" * 60, "\n")

    # Apply decision strategies if provided
    if decision_strategies:
        for strategy in decision_strategies:
            var_names = strategy["variables"]
            if isinstance(var_names, str):
                var_list = vars_.get(var_names, [])
            elif isinstance(var_names, list):
                var_list = []
                for var_name in var_names:
                    var_list.extend(vars_.get(var_name, []))
            else:
                raise ValueError("The 'variables' field must be a string or list of strings.")

            model.AddDecisionStrategy(
                var_list,
                strategy["variable_strategy"],
                strategy["value_strategy"]
            )

    # Solve
    status = solver.Solve(model)

    landing_time = vars_["landing_time"]
    early_deviation = vars_["early_deviation"]
    late_deviation = vars_["late_deviation"]
    runway_i = vars_["runway_i"]

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        plane_ids = [str(i) for i in range(num_planes)]
        l_times = [f"{solver.Value(landing_time[i]):.2f}" for i in range(num_planes)]
        earliest = [f"{planes_data[i]['earliest_landing_time']:.2f}" for i in range(num_planes)]
        targets = [f"{planes_data[i]['target_landing_time']:.2f}" for i in range(num_planes)]
        latest = [f"{planes_data[i]['latest_landing_time']:.2f}" for i in range(num_planes)]
        runways = [str(solver.Value(runway_i[i])) for i in range(num_planes)]

        w_plane = max(len("Plane"), max(len(pid) for pid in plane_ids))
        w_landing = max(len("Landing Time"), max(len(lt) for lt in l_times))
        w_earliest = max(len("Earliest"), max(len(e) for e in earliest))
        w_target = max(len("Target"), max(len(t) for t in targets))
        w_latest = max(len("Latest"), max(len(l) for l in latest))
        w_runway = max(len("Runway"), max(len(rw) for rw in runways))

        print("-> Landing times of all planes:")
        header = f"{'Plane':>{w_plane}} | {'Landing Time':>{w_landing}} | {'Earliest':>{w_earliest}} | {'Target':>{w_target}} | {'Latest':>{w_latest}} | {'Runway':>{w_runway}}"
        print(header)
        print("-" * len(header))

        for i in range(num_planes):
            print(f"{i:>{w_plane}} | {solver.Value(landing_time[i]):>{w_landing}.2f} | "
                  f"{planes_data[i]['earliest_landing_time']:>{w_earliest}.2f} | "
                  f"{planes_data[i]['target_landing_time']:>{w_target}.2f} | "
                  f"{planes_data[i]['latest_landing_time']:>{w_latest}.2f} | "
                  f"{solver.Value(runway_i[i]):>{w_runway}d}")

        # Planes that did not land on target time
        early_dev_list = [solver.Value(early_deviation[i]) for i in range(num_planes)]
        late_dev_list = [solver.Value(late_deviation[i]) for i in range(num_planes)]
        penalty_list = [early_dev_list[i]*planes_data[i]['penalty_early'] + late_dev_list[i]*planes_data[i]['penalty_late'] 
                        for i in range(num_planes)]

        plane_ids2 = [str(i) for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
        l_times2 = [f"{solver.Value(landing_time[i]):.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
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
                print(f"{i:>{w_plane2}} | {solver.Value(landing_time[i]):>{w_landing2}.2f} | "
                      f"{planes_data[i]['target_landing_time']:>{w_target2}.2f} | "
                      f"{early_dev_list[i]:>{w_early}.2f} | {late_dev_list[i]:>{w_late}.2f} | "
                      f"{penalty_list[i]:>{w_penalty}.2f}")

        if not any_missed:
            print("(none)")

        # Print objective / status
        if status == cp_model.OPTIMAL:
            print(f"\n-> Optimal Cost: {solver.ObjectiveValue()}")
        else:
            print("\n-> No optimal solution found. Best feasible:", round(solver.ObjectiveValue(), 2))
    else:
        print("\n-> No feasible/optimal solution found. Status:", solver.StatusName(status))

    metrics = {}

    return solver, model, vars_, metrics