import json, os

def read_airland_file(filename):
    with open(filename, 'r') as file:
        lines = [line.strip() for line in file if line.strip()]
    p, freeze_time = map(int, lines[0].split())

    planes = []
    index = 1
    separation_times = [[0] * p for _ in range(p)]

    for i in range(p):
        data = lines[index].split()
        index += 1

        plane = {
            'id': index,
            'appearance_time': int(data[0]),
            'earliest_landing_time': int(data[1]),
            'target_landing_time': int(data[2]),
            'latest_landing_time': int(data[3]),
            'penalty_early': float(data[4]),
            'penalty_late': float(data[5]),
        }
        planes.append(plane)
        separation_values = []
        while len(separation_values) < p :
            separation_values.extend(map(int, lines[index].split()))
            index += 1
        for j in range(p):
            separation_times[i][j] = separation_values[j]

    return {
        'p': p,
        'freeze_time': freeze_time,
        'planes': planes,
        'separation_times': separation_times
    }

def generate_separation_between_runways(num_planes, num_runways, separation_same_runway=None, default_between_runways=0):
    separation_between_runways = [[0 for _ in range(num_planes)] for _ in range(num_planes)]

    for i in range(num_planes):
        for j in range(num_planes):
            if i == j:
                separation_between_runways[i][j] = 0
            else:
                if separation_same_runway:
                    separation_between_runways[i][j] = default_between_runways
                else:
                    separation_between_runways[i][j] = default_between_runways

    return separation_between_runways

def save_solution(solver, variables, num_planes, data, solution_file, tag, dataset_name, num_runways=None, landing_times_override=None, fixed_runways = None):

    if landing_times_override is None:
        landing_time_vars = variables["landing_time"]

    # Load existing solutions
    if os.path.exists(solution_file):
        with open(solution_file, "r") as f:
            solutions = json.load(f)
    else:
        solutions = {}

    if tag not in solutions:
        solutions[tag] = []

    landing_times = []
    penalty_planes = []

    for i in range(num_planes):

        if landing_times_override is not None:
            t = round(landing_times_override[i],2)
        elif tag.startswith("MIP"):
            t = landing_time_vars[i].solution_value()
        elif tag.startswith("CP"):
            t = solver.Value(landing_time_vars[i])
        else:
            raise ValueError(f"Unknown tag format: {tag}")

        earliest = round(data[i]["earliest_landing_time"],2)
        target   = round(data[i]["target_landing_time"],2)
        latest   = round(data[i]["latest_landing_time"],2)

        runway_assigned = 0
        if tag.startswith("MIP") and "landing_runway" in variables:
            for r in range(num_runways):
                val = variables["landing_runway"][(i, r)].solution_value()
                if round(val) == 1:
                    runway_assigned = r
                    break
        elif tag.startswith("CP") and "runway_i" in variables:
            runway_assigned = solver.Value(variables["runway_i"][i])
        elif fixed_runways is not None:
            runway_assigned = fixed_runways[i]

        landing_times.append({
            "plane": i,
            "landing_time": float(t),
            "earliest": earliest,
            "target": target,
            "latest": latest,
            "runway": runway_assigned
        })

        early = round(max(0.0, target - t),2)
        late  = round(max(0.0, t - target),2)

        if early > 0 or late > 0:
            penalty_planes.append({
                "plane": i,
                "landing_time": float(t),
                "target": target,
                "early_deviation": float(early),
                "late_deviation": float(late),
                "penalty": float(
                    early * data[i]["penalty_early"] +
                    late  * data[i]["penalty_late"]
                )
            })

    if num_runways is not None:
        solutions[tag].append({
            "file": dataset_name,
            "num_runways": num_runways,
            "landing_times": landing_times,
            "penalty_planes": penalty_planes
        })
    else:
        solutions[tag].append({
            "file": dataset_name,
            "landing_times": landing_times,
            "penalty_planes": penalty_planes
        })

    with open(solution_file, "w") as f:
        json.dump(solutions, f, indent=4)

