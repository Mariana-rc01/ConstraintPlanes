# Aircraft Landing Problem

## Grade: 20.56/20 :star::star::star:

## Authors

Mariana Rocha Cristino - up202502528
Patrícia Crespo da Silva - up202202895

## Context

This project studies the **Aircraft Landing Problem (ALP)**, focusing on the scheduling of aircraft landing times and runway assignments under time-window and safety separation constraints.

Three optimization approaches are implemented and compared:

* **Mixed-Integer Programming (MIP)**
* **Constraint Programming (CP)**
* **Hybrid Logic-Based Benders Decomposition (CP–LP)**

Both **single-runway** and **multi-runway** scenarios are considered.
The goal is to minimize total penalty costs due to early or late landings while ensuring safe and feasible schedules.

The project includes model implementations, performance evaluation, and result visualization on standard benchmark datasets.

## Project Structure

```
src/
│
├── data/
│   ├── airland1.txt
│   ├── ...
│   └── airland13.txt
│
├── models/
│   ├── CP.py
│   ├── Hybrid.py
│   └── MIP.py
│
├── others/
│   ├── performance.py
│   ├── utils.py
│   └── visualization.py
│
├── results/
│   ├── metrics.json
│   └── solutions.json
│
└── Results&Analysis.ipynb
```

## Folder and File Description

### `data/`

Contains benchmark instances from **airland1.txt** to **airland13.txt**.
Each file describes aircraft landing windows, target times, penalties, and separation requirements.

### `models/`

* **CP.py**
  Implements the Constraint Programming model using CP-SAT.
  Handles sequencing, runway assignment, and search strategies.

* **MIP.py**
  Implements the Mixed-Integer Programming formulation.
  Includes single-runway and multi-runway models.

* **Hybrid.py**
  Implements the Hybrid Logic-Based Benders Decomposition.
  Uses a CP master problem and an LP subproblem with Benders cuts.

### `others/`

* **performance.py**
  Collects execution time, memory usage, and solvers' performance metrics.

* **utils.py**
  Provides data parsing, helper functions, and shared utilities.

* **visualization.py**
  Generates plots and visual representations of landing schedules.

### `results/`

* **metrics.json**
  Stores performance metrics' results for all models and datasets.

* **solutions.json**
  Stores computed landing schedules and runway assignments.

### `Results&Analysis.ipynb`

Jupyter notebook for result analysis.
Includes tables, plots, and comparative evaluation of MIP, CP, and Hybrid models.
