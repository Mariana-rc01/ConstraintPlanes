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
