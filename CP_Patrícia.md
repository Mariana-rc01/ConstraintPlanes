# Constraint Programming

## Single Runway

### Índices e conjuntos
P: número de aviões
𝑖,𝑗∈{1,…,𝑃}, 1 diferente de j
𝑈: pares(𝑖,𝑗) onde a ordem é incerta
𝑉: pares (𝑖,𝑗) onde é certo que 𝑖 aterra antes de 𝑗, mas a separação não é automaticamente garantida
𝑊: pares (𝑖,𝑗) onde é certo que 𝑖 aterra antes de 𝑗 e a separação é automaticamente garantida

### Parâmetros
𝐸𝑖 ∈ R: Instante mais cedo em que o avião 𝑖 pode aterrar, assumindo voo à velocidade máxima.
𝐿𝑖 ∈ 𝑅: Instante mais tardio em que o avião 𝑖 pode aterrar, considerando restrições de combustível e tempo máximo de espera.
𝑇𝑖 ∈ 𝑅: Instante alvo (ou preferido) de aterragem do avião 𝑖, correspondente à velocidade de cruzeiro mais económica.
𝑆𝑖𝑗≥0: Tempo mínimo de separação exigido entre a aterragem do avião 𝑖 e a aterragem subsequente do avião 𝑗
𝑔𝑖≥0: Custo marginal por unidade de tempo associado a aterrar antes do instante alvo 
ℎ𝑖≥0: Custo marginal por unidade de tempo associado a aterrar depois do instante alvo 

### Variáveis de decisão
𝑥𝑖∈[𝐸𝑖,𝐿𝑖]: tempo de aterragem do avião 𝑖
αi∈[0,Ti−Ei]: adiantamento (earliness) do avião i
𝛽𝑖∈[0,𝐿𝑖−𝑇𝑖]: atraso (tardiness) do avião i
Para cada par (𝑖,𝑗)∈𝑈 com  𝑖<𝑗:𝑏𝑒𝑓𝑜𝑟𝑒𝑖𝑗∈{0,1}∈{0,1}: 1 se 𝑖 aterra antes de 𝑗; 0 caso contrário

### Objective

min ∑(𝑔𝑖𝛼𝑖+ℎ𝑖𝛽𝑖)

### Contraints

Janela Temporal: 𝐸𝑖≤𝑥𝑖≤L𝑖 , ∀i ∈ P
Pares com ordem incerta: beforeij + beforeji = 1 para todo (i,j) pertencente a U, i<j
Earliness: αi​=max(0, Ti​−xi​)∀i
Tardiness: βi​=max(0, xi​−Ti​)∀i
Pares com ordem certa, mas não automática: xj​≥xi​+Sij​∀(i,j)∈V
Separação reificada para pares incertos:
beforeij​=1⇒xj​≥xi​+Sij​∀(i,j)∈U, i<j
beforeji​=1⇒xi​≥xj​+Sji​∀(i,j)∈U, i<j

### Domínios das variáveis
xi​∈Z, αi​,βi​∈Z≥0​, beforeij​,beforeji​∈{0,1}


## Multiple Runway

### Parâmetros adicionais
R: número de pistas
𝑠𝑖𝑗≥0: separação mínima se 𝑖 aterra antes de 𝑗 em pistas diferentes

### Aditional Variables
ri∈{1,…,R}: pista atribuída ao avião 𝑖

### Constraints
Pares de ordem fixa:
(ri​ dif rj​)⇒xj​≥xi​+Sij​∀(i,j)∈V
(ri​ dif rj​)⇒xj​≥xi​+sij​∀(i,j)∈V

Pares de ordem incerta:
(beforeij​=1∧ri​=rj​)⇒xj​≥xi​+Sij​∀(i,j)∈U, i<j
(beforeij​=1∧ri​=rj​)⇒xj​≥xi​+sij​∀(i,j)∈U, i<j
(beforeji​=1∧ri​=rj​)⇒xi​≥xj​+Sji​∀(i,j)∈U, i<j
(beforeji​=1∧ri​=rj​)⇒xi​≥xj​+sji​∀(i,j)∈U, i<j

### Domínio extra:
ri​∈{1,…,R}∀i