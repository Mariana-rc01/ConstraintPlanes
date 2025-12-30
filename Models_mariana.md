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
