import math
import time
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp

# 0. HELPER FUNCTIONS (Sets & Reading)
def calculate_sets(num_planes, planes_data, separation_times):
    W, V, U = [], [], []
    for i in range(num_planes):
        for j in range(num_planes):
            if i == j: continue
            E_i, L_i = planes_data[i]['earliest_landing_time'], planes_data[i]['latest_landing_time']
            E_j, L_j = planes_data[j]['earliest_landing_time'], planes_data[j]['latest_landing_time']
            S_ij = separation_times[i][j]

            if L_i < E_j and L_i + S_ij <= E_j:
                W.append((i, j))
            elif L_i < E_j and L_i + S_ij > E_j:
                V.append((i, j))
            else:
                U.append((i, j))
    return W, V, U

# 1. SUB-PROBLEM (LP - Linear Programming)
def solve_subproblem_lp(num_planes, planes_data, separation_times, separation_between_runways,
                        fixed_runways, fixed_before, W, V, U):
    solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver: return "ERROR", 0, []

    x = []
    alpha = []
    beta = []
    infinity = solver.infinity()

    # Create Variables
    for i in range(num_planes):
        x.append(solver.NumVar(planes_data[i]['earliest_landing_time'],
                               planes_data[i]['latest_landing_time'], f'x_{i}'))
        alpha.append(solver.NumVar(0, infinity, f'alpha_{i}'))
        beta.append(solver.NumVar(0, infinity, f'beta_{i}'))

    # Constraints: Deviation Definitions
    for i in range(num_planes):
        target = planes_data[i]['target_landing_time']
        solver.Add(x[i] + alpha[i] - beta[i] == target)

    # Constraints: Separation based on fixed sequence
    all_pairs = W + V + U
    for i, j in all_pairs:
        is_preceding = False

        # Check Precedence
        if (i, j) in W or (i, j) in V:
            is_preceding = True
        elif (i, j) in U:
            if fixed_before.get((i, j)) == 1:
                is_preceding = True

        if is_preceding:
            r_i = fixed_runways[i]
            r_j = fixed_runways[j]
            delta = separation_times[i][j] if r_i == r_j else separation_between_runways[i][j]
            solver.Add(x[j] >= x[i] + delta)

    # Objective
    objective = solver.Objective()
    for i in range(num_planes):
        objective.SetCoefficient(alpha[i], planes_data[i]['penalty_early'])
        objective.SetCoefficient(beta[i], planes_data[i]['penalty_late'])
    objective.SetMinimization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        times = [x[i].solution_value() for i in range(num_planes)]
        return "OPTIMAL", solver.Objective().Value(), times
    elif status == pywraplp.Solver.INFEASIBLE:
        return "INFEASIBLE", 0, []
    else:
        return "OTHER", 0, []

# 2. MASTER PROBLEM (CP - Strengthened)
def solve_hybrid_lbbd(num_planes, num_runways, planes_data, separation_times, separation_between_runways, max_iterations=20):
    print("\n" + "=" * 60)
    print("\t\tRunning Hybrid LBBD Solver (Strengthened Master)")
    print("=" * 60, "\n")

    start_time = time.time()
    W, V, U = calculate_sets(num_planes, planes_data, separation_times)

    master_model = cp_model.CpModel()

    # Discrete Decision Variables
    r = [master_model.NewIntVar(1, num_runways, f'r_{i}') for i in range(num_planes)]
    before = {}
    for i, j in U:
        if (i, j) not in before:
            before[(i, j)] = master_model.NewBoolVar(f'before_{i}_{j}')
        if (j, i) not in before:
            before[(j, i)] = master_model.NewBoolVar(f'before_{j}_{i}')

    # Mutually Exclusive: Either i before j OR j before i
    for i, j in U:
        master_model.Add(before[(i, j)] + before[(j, i)] == 1)

    # B. Proxy Time Variables (Strengthened Master)
    # These allow the Master to estimate costs BEFORE calling the LP
    x_m = []
    alpha_m = []
    beta_m = []
    max_time = max(p['latest_landing_time'] for p in planes_data)

    for i in range(num_planes):
        # Time Windows
        x_m.append(master_model.NewIntVar(planes_data[i]['earliest_landing_time'],
                                          planes_data[i]['latest_landing_time'], f'xm_{i}'))
        alpha_m.append(master_model.NewIntVar(0, max_time, f'am_{i}'))
        beta_m.append(master_model.NewIntVar(0, max_time, f'bm_{i}'))

        # Link Deviation to Time (Integer Relaxation)
        tgt = planes_data[i]['target_landing_time']
        master_model.Add(x_m[i] + alpha_m[i] - beta_m[i] == tgt)

    # Cost Calculation in Master
    # We sum up the penalties. Note: CP works with Integers, so penalties must be int here.
    # If penalties are floats (e.g. 1.5), multiply everything by 10 or 100.
    master_cost = sum(alpha_m[i] * int(planes_data[i]['penalty_early']) +
                      beta_m[i] * int(planes_data[i]['penalty_late']) for i in range(num_planes))

    # Theta variable (Estimator for Benders)
    # Theta must be at least the cost calculated by the Master itself
    theta = master_model.NewIntVar(0, int(1e7), 'theta')
    master_model.Add(theta >= master_cost)
    master_model.Minimize(theta)

    # Logic Constraints (Sequence)
    processed = set()
    for i, j in U:
        pair = tuple(sorted((i, j)))
        if pair in processed: continue
        processed.add(pair)
        # Mutually Exclusive: Either i before j OR j before i
        master_model.Add(before[(i, j)] + before[(j, i)] == 1)

    # Time/Separation Constraints in Master
    # This guides the Master to choose valid sequences

    # 1. Uncertain Pairs (U)
    for i, j in U:
        # Reification: Are they on the same runway?
        same_rw = master_model.NewBoolVar(f'same_{i}_{j}')
        master_model.Add(r[i] == r[j]).OnlyEnforceIf(same_rw)
        master_model.Add(r[i] != r[j]).OnlyEnforceIf(same_rw.Not())

        # If i before j:
        # Same Runway -> S_ij
        master_model.Add(x_m[j] >= x_m[i] + separation_times[i][j]).OnlyEnforceIf([before[(i,j)], same_rw])
        # Diff Runway -> s_ij
        master_model.Add(x_m[j] >= x_m[i] + separation_between_runways[i][j]).OnlyEnforceIf([before[(i,j)], same_rw.Not()])

    # 2. Certain Order Pairs (V)
    for i, j in V:
        same_rw = master_model.NewBoolVar(f'same_{i}_{j}')
        master_model.Add(r[i] == r[j]).OnlyEnforceIf(same_rw)
        master_model.Add(r[i] != r[j]).OnlyEnforceIf(same_rw.Not())

        master_model.Add(x_m[j] >= x_m[i] + separation_times[i][j]).OnlyEnforceIf(same_rw)
        master_model.Add(x_m[j] >= x_m[i] + separation_between_runways[i][j]).OnlyEnforceIf(same_rw.Not())

    # Main Loop
    solver = cp_model.CpSolver()
    # solver.parameters.log_search_progress = True # Optional: see CP logs

    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"--- Iteration {iteration} ---")

        status = solver.Solve(master_model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("Master problem INFEASIBLE.")
            break

        current_theta = solver.Value(theta)

        # Extract Solution
        fixed_runways = [solver.Value(r[i]) for i in range(num_planes)]
        fixed_before = {}
        for i, j in U:
            fixed_before[(i, j)] = solver.Value(before[(i, j)])

        # Solve Subproblem (LP)
        sp_status, sp_cost, sp_times = solve_subproblem_lp(
            num_planes, planes_data, separation_times, separation_between_runways,
            fixed_runways, fixed_before, W, V, U
        )

        # Function to create boolean literals for cuts
        def create_literals():
            lits = []
            for i in range(num_planes):
                # Reify Integer variable r[i]
                b = master_model.NewBoolVar(f'reify_r{i}_it{iteration}')
                val = fixed_runways[i]
                master_model.Add(r[i] == val).OnlyEnforceIf(b)
                master_model.Add(r[i] != val).OnlyEnforceIf(b.Not())
                lits.append(b)
            for (i,j), val in fixed_before.items():
                lits.append(before[(i,j)] if val else before[(i,j)].Not())
            return lits

        if sp_status == "INFEASIBLE":
            print(f"  >> Subproblem INFEASIBLE (Should be rare with Strengthened Master).")
            lits = create_literals()
            master_model.AddBoolOr([l.Not() for l in lits])

        elif sp_status == "OPTIMAL":
            sp_cost_int = math.ceil(sp_cost)
            print(f"  >> Master Theta: {current_theta} | Subproblem Real Cost: {sp_cost_int}")

            # Check Convergence
            # Tolerance 1e-4 for float issues
            if sp_cost_int <= current_theta + 1e-4:
                print(f"\n*** CONVERGENCE ACHIEVED in {iteration} iterations! ***")
                print_solution(sp_times, fixed_runways, sp_cost, num_planes, planes_data)
                break
            else:
                print(f"  >> Gap found. Adding Optimality Cut.")
                lits = create_literals()
                is_same = master_model.NewBoolVar(f'match_{iteration}')
                master_model.AddBoolAnd(lits).OnlyEnforceIf(is_same)
                master_model.AddBoolOr([l.Not() for l in lits]).OnlyEnforceIf(is_same.Not())

                # Benders Cut
                master_model.Add(theta >= sp_cost_int).OnlyEnforceIf(is_same)

    metrics = {}
    return solver, master_model, sp_times, metrics

def print_solution(times, runways, cost, num_planes, planes_data):
    plane_ids = [str(i) for i in range(num_planes)]
    landing_times = [f"{times[i]:.2f}" for i in range(num_planes)]
    earliest = [f"{planes_data[i]['earliest_landing_time']:.2f}" for i in range(num_planes)]
    targets = [f"{planes_data[i]['target_landing_time']:.2f}" for i in range(num_planes)]
    latest = [f"{planes_data[i]['latest_landing_time']:.2f}" for i in range(num_planes)]
    runways = [str(runways[i]) for i in range(num_planes)]

    w_plane = max(len("Plane"), max(len(pid) for pid in plane_ids))
    w_landing = max(len("Landing Time"), max(len(lt) for lt in landing_times))
    w_earliest = max(len("Earliest"), max(len(e) for e in earliest))
    w_target = max(len("Target"), max(len(t) for t in targets))
    w_latest = max(len("Latest"), max(len(l) for l in latest))
    w_runway = max(len("Runway"), max(len(rw) for rw in runways))

    print("\n-> Landing times of all planes:")
    header = f"{'Plane':>{w_plane}} | {'Landing Time':>{w_landing}} | {'Earliest':>{w_earliest}} | {'Target':>{w_target}} | {'Latest':>{w_latest}} | {'Runway':>{w_runway}}"
    print(header)
    print("-" * len(header))

    for i in range(num_planes):
        print(f"{i:>{w_plane}} | {times[i]:>{w_landing}.2f} | "
              f"{planes_data[i]['earliest_landing_time']:>{w_earliest}.2f} | "
              f"{planes_data[i]['target_landing_time']:>{w_target}.2f} | "
              f"{planes_data[i]['latest_landing_time']:>{w_latest}.2f} | "
              f"{runways[i]:>{w_runway}}")

    # Planes that did NOT land on target time
    early_dev_list = [max(0.0, planes_data[i]['target_landing_time'] - times[i]) for i in range(num_planes)]
    late_dev_list = [max(0.0, times[i] - planes_data[i]['target_landing_time']) for i in range(num_planes)]
    penalty_list = [early_dev_list[i]*planes_data[i]['penalty_early'] + late_dev_list[i]*planes_data[i]['penalty_late']
                    for i in range(num_planes)]

    plane_ids2 = [str(i) for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    landing_times2 = [f"{times[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    targets2 = [f"{planes_data[i]['target_landing_time']:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    early_dev_str = [f"{early_dev_list[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    late_dev_str = [f"{late_dev_list[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    penalty_str = [f"{penalty_list[i]:.2f}" for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]
    runways2 = [str(runways[i]) for i in range(num_planes) if early_dev_list[i] > 0 or late_dev_list[i] > 0]

    w_plane2 = max(len("Plane"), max(len(pid) for pid in plane_ids2) if plane_ids2 else 0)
    w_landing2 = max(len("Landing Time"), max(len(lt) for lt in landing_times2) if landing_times2 else 0)
    w_target2 = max(len("Target"), max(len(t) for t in targets2) if targets2 else 0)
    w_early = max(len("Early Dev"), max(len(ed) for ed in early_dev_str) if early_dev_str else 0)
    w_late = max(len("Late Dev"), max(len(ld) for ld in late_dev_str) if late_dev_str else 0)
    w_penalty = max(len("Penalty"), max(len(pen) for pen in penalty_str) if penalty_str else 0)
    w_runway2 = max(len("Runway"), max(len(rw) for rw in runways2) if runways2 else 0)

    print("\n-> Planes that did not land on the target time:")
    header2 = f"{'Plane':>{w_plane2}} | {'Landing Time':>{w_landing2}} | {'Target':>{w_target2}} | {'Early Dev':>{w_early}} | {'Late Dev':>{w_late}} | {'Penalty':>{w_penalty}} | {'Runway':>{w_runway2}}"
    print(header2)
    print("-" * len(header2))

    for i in range(num_planes):
        if early_dev_list[i] > 0 or late_dev_list[i] > 0:
            print(f"{i:>{w_plane2}} | {times[i]:>{w_landing2}.2f} | {planes_data[i]['target_landing_time']:>{w_target2}.2f} | "
                  f"{early_dev_list[i]:>{w_early}.2f} | {late_dev_list[i]:>{w_late}.2f} | "
                  f"{penalty_list[i]:>{w_penalty}.2f} | {runways[i]:>{w_runway2}}")

    print("\n" + "=" * 60)
    print(f"TOTAL COST = {cost:.2f}")
    print("=" * 60)

