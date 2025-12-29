To-Do List: (at least)
  MIP:

- [X] Design of the model
- [X] Implementation of the model
- [X] Test of the model

  CP:
- [ ] Design of the model
- [ ] Implementation of the model
- [ ] Test of the model

  Comparison between the MIP and CP models:
- [ ] Comparing both the solutions (to check for correctness)
- [ ] Comparing the running times (to check for efficiency) of the model

  Others:
- [ ] Fazer gráfico das differentes formas de search strategies
- [ ] Valor ótimo de multiple runways
- [ ] Fazer junção do MIP com o CP

Notes:

- You can compare CP models using the basic and the more compact constraints on your problem instances.
- You should also analyze the impact of different search options for CP.

Ideias:

- visualização interativa ou dinâmica da sequência dos aviões a aterrarem para um certo conjunto de dados (fica bem visualmente para até 30 aviões, mais pode ser confuso)

Interpretação dos ficheiros:
number of planes (p), freeze time
for each plane i (i=1,...,p):
   appearance time, earliest landing time, target landing time,
   latest landing time, penalty cost per unit of time for landing
   before target, penalty cost per unit of time for landing
   after target
   for each plane j (j=1,...p): separation time required after
                                i lands before j can land

The value of the optimal solution for each of these data
files for a varying number of runways is given in the
above papers.
