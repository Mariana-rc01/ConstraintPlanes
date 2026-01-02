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

## 1. Motivation and Context
The Aircraft Landing Problem (ALP) is a classic combinatorial optimization challenge classified as NP-Hard. It requires assigning aircraft to runways, determining the landing sequence, and scheduling precise landing times within specific time windows \([E_i, L_i]\) to minimize deviations from a target time \(T_i\).

Traditional approaches often face significant computational hurdles:

- **Pure Mixed-Integer Programming (MIP):** Relies heavily on "Big-M" constraints to model disjunctive logic (e.g., "Plane A lands before B" OR "B before A"). These constraints result in weak linear relaxations, causing the branch-and-bound search tree to explode in size for large instances.

- **Pure Constraint Programming (CP):** While excellent at handling logical constraints and finding feasible sequences efficiently, CP often struggles to prove optimality in problems with complex objective functions involving continuous costs (penalties).

To overcome these limitations, a **Hybrid Logic-Based Benders Decomposition (LBBD)** was implemented. This approach leverages the complementary strengths of both paradigms:

- **CP:** Handles the combinatorial structure (sequencing and assignment).
- **LP:** Handles the numerical optimization (precise timing).

## 2. The Core Idea: Decomposition
The central concept of LBBD is to decompose the monolithic problem into two hierarchical levels that communicate iteratively:

- **The Master Problem (CP):** Acts as the "Architect." Decides the structure of the solution—runway assignments and landing order—using integer variables to enforce logical constraints.

- **The Subproblem (LP):** Acts as the "Surveyor." Given the fixed structure from the Master, calculates optimal continuous landing times using linear optimization.

- **Benders Cuts (Feedback):** If the Master proposes an infeasible or costly sequence, the Subproblem generates a cut—a constraint added to the Master—saying, e.g., "Do not try this specific configuration again" or "This configuration costs at least X."

## 3. Mathematical Formulation: Strengthened Hybrid LBBD
This model differs from classical LBBD by including **proxy time variables** in the Master Problem. These variables allow the Master to estimate costs and ensure basic temporal feasibility before consulting the Subproblem, acting as a **Strengthened Master**.

### 3.1. Sets and Parameters

**Indices and Sets:**
- \(P = \{1, \dots, P\}\): Set of aircraft.
- \(R = \{1, \dots, R\}\): Set of available runways.
- \(U\): Set of pairs \((i,j)\) where landing order is uncertain.
- \(V\): Set of pairs \((i,j)\) where \(i\) precedes \(j\) (fixed order) but separation is not automatically guaranteed.
- \(W\): Set of pairs \((i,j)\) where \(i\) precedes \(j\) and separation is implicitly guaranteed by time windows.

**Parameters:**
- \(E_i, L_i, T_i\): Time window \([E_i, L_i]\) and target time \(T_i\) for aircraft \(i\).
- \(g_i, h_i\): Penalty costs per unit of time for earliness and lateness.
- \(S_{ij}\): Minimum separation time if \(i\) precedes \(j\) on the same runway.
- \(s_{ij}\): Minimum separation time if \(i\) precedes \(j\) on different runways.

### 3.2. Master Problem (CP - Strengthened)
The Master decides sequencing and allocation, using relaxed (integer) time variables to strengthen the lower bound of the objective function.

**Decision Variables:**
- \(r_i \in R\): Runway assigned to aircraft \(i\).
- \(y_{ij} \in \{0,1\}\): Precedence variable; 1 if \(i\) lands before \(j\) (for \((i,j) \in U\)).
- \(\theta \ge 0\): Auxiliary variable for estimated total cost (Benders variable).

**Proxy Variables (Strengthening):**
- \(x_i^m \in [E_i, L_i]\): Approximate landing time (integer).
- \(\alpha_i^m, \beta_i^m \ge 0\): Approximate time deviations (integer).

**Objective Function:**
\[
\min \theta
\]

**Constraints:**
1. **Sequencing Logic:**
   \[
   y_{ij} + y_{ji} = 1, \quad \forall (i,j) \in U
   \]

2. **Proxy Deviation Definition:**
   \[
   x_i^m + \alpha_i^m - \beta_i^m = T_i, \quad \forall i \in P
   \]

3. **Logical Separation Constraints (Strengthening):**
   For pairs where \(i\) precedes \(j\) (\((i,j) \in V\) or \(y_{ij} = 1\)):

   - If same runway (\(r_i = r_j\)):
     \[
     x_j^m \ge x_i^m + S_{ij}
     \]
   - If different runways (\(r_i \ne r_j\)):
     \[
     x_j^m \ge x_i^m + s_{ij}
     \]

4. **Cost Lower Bound:**
   \[
   \theta \ge \sum_{i \in P} (g_i \alpha_i^m + h_i \beta_i^m)
   \]

5. **Benders Cuts (Optimality Cuts):**
   For iteration \(k\) with solution \((\hat{r}^{(k)}, \hat{y}^{(k)})\) and subproblem cost \(Z_{SP}^{(k)}\):

   \[
   \bigwedge_{i \in P} (r_i = \hat{r}_i^{(k)}) \wedge \bigwedge_{(i,j) \in U} (y_{ij} = \hat{y}_{ij}^{(k)}) \implies \theta \ge Z_{SP}^{(k)}
   \]

   *(Feasibility cuts are applied if the Subproblem is infeasible.)*

### 3.3. Subproblem (LP)
Given fixed \(\hat{r}\) and \(\hat{y}\) from the Master, the Subproblem determines exact continuous times.

**Decision Variables:**
- \(x_i \in [E_i, L_i]\): Exact landing time (continuous).
- \(\alpha_i, \beta_i \ge 0\): Exact deviations (continuous).

**Derived Parameter:** Active Separation \(\Delta_{ij}\):
\[
\Delta_{ij} =
\begin{cases}
S_{ij} & \text{if } \hat{r}_i = \hat{r}_j \\
s_{ij} & \text{if } \hat{r}_i \ne \hat{r}_j
\end{cases}
\]

**Objective Function:**
\[
\min Z_{SP} = \sum_{i \in P} (g_i \alpha_i + h_i \beta_i)
\]

**Constraints:**
1. **Deviation Definition:**
   \[
   x_i + \alpha_i - \beta_i = T_i, \quad \forall i \in P
   \]

2. **Fixed Separation Constraints:** Applied to active precedence pairs:
   \[
   x_j \ge x_i + \Delta_{ij}
   \]

## 4. How It Functions (The Algorithm)
The interaction between Master and Subproblem follows an iterative loop:

1. **Initialization:** \(k = 0\)

2. **Master Step:** Solve the Master Problem (CP) to get \(\hat{r}, \hat{y}, \theta^*\). Proxy variables give a strong approximation of real cost.

3. **Subproblem Step:** Fix \(\hat{r}, \hat{y}\) in Subproblem (LP) and solve to obtain actual minimal cost \(Z_{SP}\).

4. **Convergence Check:**
   - If \(Z_{SP} \le \theta^* + \epsilon\): **STOP**. Optimal solution found.
   - Otherwise: Add a **Benders Cut** with value \(Z_{SP}\).

5. **Iteration:** \(k \gets k+1\), return to step 2.

**Overall Interpretation:**
By using the **Strengthened Master**, the CP model performs "Pre-Optimization." Instead of blind guessing, it provides high-quality sequences from the very first iteration. The LP then acts merely as a fine-tuning step to adjust decimal precision. This explains why the implementation often converges to the optimal solution (e.g., Cost 90) in very few iterations.
