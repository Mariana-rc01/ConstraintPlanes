# MIP

## Single Runway

Indices and Sets:
i, j - índices para os aviões (i=1,...,P, j=1,...,P)
U - set de pares (i,j) de aviões onde é incerto se o avião i aterra antes do avião j ou não
V - set de pares (i,j) de aviões onde é certo que o avião i aterra antes do que o avião j, mas onde a separation constraint não é automaticamente cumprida
W - set de pares (i,j) de aviões onde é certo que o avião i aterra antes do que o avião j, mas onde a separation constraint é automaticamente cumprida

Parameters:
P - número de aviões
E_i - o tempo mais cedo para o avião i, i=1,...,P
L_i - o tempo mais tardio para o avião i, i=1,...,P
T_i - o tempo que se pretende alcançar (target time) do avião i, i=1,...,P
S_ij - (>= 0) o tempo de separação requerido entre a aterragem do avião i e a aterragem do avião j (quando avião i aterra antes do avião j), i != j, i=1,...,P, j=1,...,P
g_i - (>= 0) o custo de penalidade por unidade de tempo para o avião i aterrar antes do seu target time (T_i), i=1,...,P
h_i - (>= 0) o custo de penalidade por unidade de tempo para o avião i aterrar depois do seu target time (T_i), i=1,...,P

A janela de tempo para o avião i é [E_ii, L_i], onde E_i < T_i < L_i.

Variáveis de Decisão:
x_i - o tempo de aterragem do avião i, i=1,...,P
alfa_i - o quão cedo o avião i aterra antes do target time T_i, i=1,...,P
beta_i - quanto tempo o avião i aterra depois do target time T_i, i=1,...,P
delta_ij = 1 se o avião i aterra antes do avião j, i != j, i=1,...,P, j=1,...,P
         = 0 otherwise

Objective:
            min T = SUM_{i=1}^P (g_i * alfa_i + h_i * beta_i)
Subject to
            E_i <= x_i <= L_i, i=1,...,P (1)
            delta_ij + delta_ji = 1, i < j, i=1,...,P, j=1,...,P (2) (ou aterra primeiro i ou aterra primeiro j)
            delta_ij = 1, Forall(i,j) ∈ W **U** V (3)
            x_j >= x_i + S_ij, Forall(i,j) ∈ V (4)
            x_j >= x_i + S_ij * delta_ij - (L_i - E_j) * delta_ij, Forall(i,j) ∈ U (5)
            alfa_i >= T_i - x_i, i=1,..., (6)
            0 <= alfa_i <= T_i - E_i, i=1,..., (7)
            beta_i >= x_i - T_i, i=1,..., (8)
            0 <= beta_i <= L_i - T_i, i=1,..., (9)
            x_i = T_i - alfa_i + beta_i, i=1,..., (10)
            alfa_i, beta_i >= 0, x_i >=0, delta_ij ∈ {0,1}, Forall(i,j)
Sets:
            W = [(i,j) | L_i < E_j and L_i + S_ij <= E_j, where i != j, i=1,...,P, j=1,...,P]
            V = [(i,j) | L_i < E_j and L_i + S_ij > E_j, where i != j, i=1,...,P, j=1,...,P]
            U = [(i,j) | i != j, i=1,...,P, j=1,...,P, E_j<=E_i<=L_j or E_j<=L_i<=L_j or E_i<=E_j<=L_i or E_i<=L_j<=L_i]

Type of constraints:
(1) - time-window
(2) - landing order
(3), (4), (5) - separation (fazer a dedução da (5) no report)
(7) ... (10) - deviation definition

## Adições para Multiple Runways

Indices and Sets:
r - índice para a pista de aterragem (r=1,...,R)

Parameters:
R - número de pistas
s_ij - (>= 0) o tempo de separação requerido entre a aterragem do avião i e a aterragem do avião j (quando avião i aterra antes do avião j **em diferentes runways**), i != j, i=1,...,P, j=1,...,P

Decision Variables
y_ir = 1 se o avião i aterra na runway r, i=1,...,P, r=1,...,R
     = 0 otherwise
z_ij = 1 se o avião i e o avião j aterram na mesma runway, i != j, i=1,...,P, j=1,...,P
     = 0 otherwise

Novas Constraints:
            SUM_{r=1}^R y_ir = 1, i=1,...,P (11)
            z_ij = z_ji, i < j, i=1,...,P, j=1,...,P (12)
            z_ij >= y_ir + y_jr - 1, i < j, i=1,...,P, j=1,...,P, r=1,...,P (13)
            y_ir ∈ {0,1}, z_ij ∈ {0,1}, Forall(i,j,r)
Substituições de Constraints:
            x_j >= x_i + S_ij * z_ij + s_ij * (1- z_ij), Forall(i,j) ∈ V (14) - sai a (4)
            x_j >= x_i + S_ij * z_ij - (L_i + max(S_ij, s_ij) - E_j) * delta_ij, Forall(i,j) ∈ U (15) - sai a (5)

Fazer dedução da (15) no report

# CP

## Single Runway

Indices and Sets:
i, j - índices para os aviões (i=1,...,P, j=1,...,P)
U - set de pares (i,j) de aviões onde é incerto se o avião i aterra antes do avião j ou não
V - set de pares (i,j) de aviões onde é certo que o avião i aterra antes do que o avião j, mas onde a separation constraint não é automaticamente cumprida
W - set de pares (i,j) de aviões onde é certo que o avião i aterra antes do que o avião j, mas onde a separation constraint é automaticamente cumprida

Parameters:
P - número de aviões
E_i - o tempo mais cedo para o avião i, i=1,...,P
L_i - o tempo mais tardio para o avião i, i=1,...,P
T_i - o tempo que se pretende alcançar (target time) do avião i, i=1,...,P
S_ij - (>= 0) o tempo de separação requerido entre a aterragem do avião i e a aterragem do avião j (quando avião i aterra antes do avião j), i != j, i=1,...,P, j=1,...,P
g_i - (>= 0) o custo de penalidade por unidade de tempo para o avião i aterrar antes do seu target time (T_i), i=1,...,P
h_i - (>= 0) o custo de penalidade por unidade de tempo para o avião i aterrar depois do seu target time (T_i), i=1,...,P

Variáveis de Decisão:
x_i - o tempo de aterragem do avião i, i=1,...,P **x_i ∈ [E_i, L_i]**
alfa_i - o quão cedo o avião i aterra antes do target time T_i, i=1,...,P **(alfa_i >= 0)**
beta_i - quanto tempo o avião i aterra depois do target time T_i, i=1,...,P **(beta_i >= 0)**
before_ij - 1 se i aterra antes de j **before_ij ∈ {0,1}**

Objective:
            min T = SUM_{i=1}^P (g_i * alfa_i + h_i * beta_i)
Subject to
            E_i <= x_i <= L_i, Forall i (1)
            before_ij + before_ji = 1, Forall i < j (2)
            alfa_i = max(0, T_i - x_i), Forall i (3)
            beta_i = max(0, x_i - T_i), Forall i (4)
            x_j >= x_i + S_ij, Forall (i,j) ∈ V (5)
            before_ij = 1 => x_j >= x_i + S_ij, Forall (i,j) ∈ U (6)
            before_ji = 1 => x_i >= x_j + S_ji, Forall (i,j) ∈ U (7)
Sets:
            W = [(i,j) | L_i < E_j and L_i + S_ij <= E_j, where i != j, i=1,...,P, j=1,...,P]
            V = [(i,j) | L_i < E_j and L_i + S_ij > E_j, where i != j, i=1,...,P, j=1,...,P]
            U = [(i,j) | i != j, i=1,...,P, j=1,...,P, E_j<=E_i<=L_j or E_j<=L_i<=L_j or E_i<=E_j<=L_i or E_i<=L_j<=L_i]

## Adições para Multiple Runways

Parameters:
R - número de pistas
s_ij - (>= 0) o tempo de separação requerido entre a aterragem do avião i e a aterragem do avião j (quando avião i aterra antes do avião j **em diferentes runways**), i != j, i=1,...,P, j=1,...,P

Decision Variables
r_i - índice da pista atribuída ao avião i **r_i ∈ {1,...,R}**

Novas Constraints:
(r_i == r_j) => x_j >= x_i + S_ij, Forall (i,j) ∈ V (8)
(r_i != r_j) => x_j >= x_i + s_ij, Forall (i,j) ∈ V (9)

(before_ij ∧ (r_i == r_j)) => x_j >= x_i + S_ij, Forall (i,j) ∈ U (10)
(before_ij ∧ (r_i != r_j)) => x_j >= x_i + s_ij, Forall (i,j) ∈ U (11)
(before_ji ∧ (r_i == r_j)) => x_i >= x_j + S_ji, Forall (i,j) ∈ U (12)
(before_ji ∧ (r_i != r_j)) => x_i >= x_j + s_ji, Forall (i,j) ∈ U (13)

Saíem as constraints (5) -> (8) e (9), (6) e (7) -> restantes

Usar no código:
- Branching Strategies
- Variable Selection Strategies
- Value Selection Strategies
- Using Hints for Optimizing Search (já a ser usado no MIP - eg line 107 e 282)

# Metrics

## MIP
- Execution Time
- Number of Variables
- Number of Constraints
- Total Penalty (Objective Value)
- Memory Usage
- Number of Branch-and-Bound Nodes

## CP
- Execution Time
- Solution Status
- Number of Conflicts
- Number of Branches
- Best Objective Bound
- Number of Propagations
- Time to First Solution
- Failures/Backtracks


# Hybrid Logic-Based Benders Decomposition (LBBD)

## 1. Motivation

The Aircraft Landing Problem is a classic combinatorial optimization challenge classified as NP-Hard. It requires assigning aircraft to runways, determining the landing sequence, and scheduling precise landing times within specific time windows to minimize deviations from a target time .

Traditional approaches often face significant computational hurdles:

* **Pure Mixed-Integer Programming (MIP):** Relies heavily on "Big-M" constraints to model disjunctive logic (e.g., "Plane A lands before B" OR "B before A"). These constraints result in weak linear relaxations, causing the branch-and-bound search tree to explode in size for large instances.
* **Pure Constraint Programming (CP):** While excellent at handling logical constraints and finding feasible sequences efficiently, CP often struggles to prove optimality in problems with complex objective functions involving continuous costs (penalties).

To overcome these limitations, it was implemented a **Hybrid Logic-Based Benders Decomposition (LBBD)**. This approach combines Constraint Programming (CP) for discrete decisions and Linear Programming (LP) for continuous scheduling and cost evaluation.

## 2. The Core Idea: Decomposition

The central concept of LBBD is to decompose the monolithic problem into two hierarchical levels that communicate iteratively:

1. **The Master Problem (CP):** Acts as the "Architect." It decides the structure of the solution—which runway to use and the order of landing—without worrying about the exact millisecond of landing.

2. **The Subproblem (LP):** Acts as the "Surveyor." Given the fixed structure provided by the Master, it calculates the optimal landing times using efficient linear optimization.

3. **Benders Cuts (Feedback):** If the Master proposes a sequence that is infeasible or too expensive, the Subproblem generates a "Cut"—a mathematical constraint added to the Master Problem—effectively saying, *"Do not try this specific configuration again,"* or *"This configuration costs at least X."*

## 3. Mathematical Formulation

### 3.1. Indices and Sets

Let:

P = {1,...,P} : Set of aircraft.
R = {1,...,R} : Set of available runways.
U : Set of pairs (i,j) where the landing order is uncertain.
V : Set of pairs where i precedes j (fixed order), but separation is not automatically guaranteed.
W : Set of pairs where i precedes j and separation is implicit (time windows do not overlap).

### 3.2. Parameters

E_i, L_i, T_i : Earliest, Latest, and Target landing times for plane .
g_i, h_i : Penalty costs per unit of time for earliness and lateness, respectively.
S_ij : Required separation time if i precedes j on the **same runway**.
s_ij : Required separation time if i precedes j on **different runways**.

### 3.3. The Master Problem (CP - Strengthened)

The Master Problem is modeled using Constraint Programming. Its goal is to minimize an auxiliary variable \theta, which represents the estimated lower bound of the total cost.

**Unique Feature: Strengthened Formulation**
Unlike standard Benders decomposition, where the Master is "blind" to time, our implementation includes **proxy time variables** (x_i^m). These are integer relaxations of the landing times. They allow the Master Problem to perform a preliminary feasibility check and cost estimation, drastically reducing the number of iterations required for convergence.

**Decision Variables:**

r_i ∈ R : The runway assigned to plane i.
y_ij ∈ {0,1} : Binary variable (mapped to `before` in code); 1 if plane i lands before j.
\theta >= 0 : The estimated total cost.

**Proxy Variables (for Strengthening):**

x_i^m ∈ [E_i, L_i] : Approximate integer landing time.
alfa_i^m, beta_i^m >= 0 : Approximate earliness and lateness.

**Constraints:**

1. **Sequencing Logic:** For all uncertain pairs, one must precede the other.

          y_ij + y_ji = 1, Forall (i,j) ∈ U

2. **Logical Separation (Proxy Time):** Enforces separation logic directly in the Master using logical implication.
If i precedes j (y_ij = 1):

          x_j^m >= x_i^m + S_ij if r_i = r_j
          x_j^m >= x_i^m + s_ij if r_i != r_j

3. **Cost Lower Bound:** The objective \theta must be at least the cost calculated by the proxy variables.

          \theta >= Sum_i∈P (g_i * alfa_i^m + h_i * beta_i^m)

4. **Benders Cuts (Optimality):** Ideally, if a configuration (r^, y^) is revisited, the cost \theta must be greater than or equal to the true cost found by the Subproblem (Z_SP).

          (Configuration = (r^, y^)) => \theta >= Z_SP


### 3.4. The Subproblem (LP)

Once the Master fixes the variables r^ (runways) and y^ (sequence), the complex disjunctive constraints disappear. The problem collapses into a continuous Linear Programming (LP) model, which is solvable in polynomial time.

**Decision Variables:**

x_i ∈ [E_i, L_i] : Exact continuous landing time.
alfa_i, beta_i >= 0 : Exact earliness and lateness.

**Derived Parameter:**
We define the active separation \delta_ij based on the Master's decision:

          \delta_ij = { S_ij, if y^_ij = 1 and r^_i = r^_j
                      { s_ij, if y^_ij = 1 and r^_i != r^_j

**Constraints:**

1. **Deviation Definition:** x_i + alfa_i - beta_i = T_i
2. **Fixed Separation:** x_j >= x_i + \delta_ij (Only applied for pairs where precedence is active).

**Objective:**

          min Z_SP = Sum_i∈P (g_i * alfa_i + h_i * beta_i)


## 4. How It Functions (The Algorithm)

The interaction between the two models follows an iterative loop:

1. **Master Step:** The CP solver finds a sequence and runway allocation. Thanks to the "Strengthened" variables, it also produces a valid integer schedule with an estimated cost .
2. **Subproblem Step:** The LP solver takes this sequence and optimizes the continuous times to find the *true* minimal cost Z_SP.
3. **Convergence Check:**
* If the Master's estimate (\theta*) equals the true cost (Z_SP), the solution is optimal. The loop terminates.
* If Z_SP > \theta*, the Master was too optimistic. An **Optimality Cut** is generated and added to the Master, effectively stating: *"For this specific sequence, the cost is actually Z_SP."*


4. **Iteration:** The process repeats with the added cut, forcing the Master to explore different parts of the solution space or adjust its cost estimation.

### Overall Interpretation

By using the **Strengthened Master**, the CP model performs "Pre-Optimization." Instead of blind guessing, it provides high-quality sequences from the very first iteration. The LP then acts merely as a fine-tuning step to adjust decimal precision. This explains why the implementation often converges to the optimal solution (e.g., Cost 90) in very few iterations.