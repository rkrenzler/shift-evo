# Optimize shifts for medical staff.
# Ruslan Krenzler 21.03.2020
# This code is under the public domain licence CC0, See https://creativecommons.org/
# It is only proof of concept.
# Calculate plan for Employees numbered 1,2,3,4,... missing employee is 0
# For days 1,2,3,4,5

import copy
import random  # For seed.
import array
import csv
import multiprocessing

import numpy
from deap import base
from deap import creator
from deap import tools
import problem as problem_mod
from evo import Helper
import metaalgorithms

# Use normal random instead of numpy.random.seed(7) to get reproducible results.
random.seed(7)

PLAN_CSV_FILE = 'plan.csv'  # Here we store the resulting file.

# Simple test problem
# problem = problem_mod.ProblemBuilder.generate(nemp=12, ndays=5, npar=2)
# Medium problem
problem = problem_mod.ProblemBuilder.generate(nemp=40, ndays=30, npar=6)

POPULATION_SIZE = 100
MAX_GENERATIONS = 10000
MAX_NO_IMPROVEMENTS = 100
# Set it to None if you do not want to write data to a file.
CSV_FILE = None

helper = Helper(problem)
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", array.array, typecode="l", fitness=creator.FitnessMin)
toolbox = base.Toolbox()
initial_solution = helper.no_one_works()
toolbox.register("initialSolution", copy.deepcopy, initial_solution)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.initialSolution)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutUniformInt, low=helper.min_decision(),
                 up=helper.max_decision(), indpb=1.0 / len(initial_solution))
toolbox.register("evaluate", helper.evaluate)
toolbox.register("select", tools.selTournament, tournsize=3)

print("Initial solution:")
ind1 = toolbox.individual()
print(ind1)
print("Initial fitness: {}".format(helper.evaluate(initial_solution)))

# Swich on multiprocessing.
pool = multiprocessing.Pool()
toolbox.register("map", pool.map)

# Solve.
pop = toolbox.population(n=POPULATION_SIZE)
hof = tools.HallOfFame(1)
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("Avg", numpy.mean)
stats.register("Std", numpy.std)
stats.register("Min", numpy.min)
T = len(initial_solution)
stats.register("MinTotal", lambda x: numpy.min(x) * T)  # Minimal total costs and not average.
stats.register("Max", numpy.max)
pop, logbook = metaalgorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.1, ngen=MAX_GENERATIONS,
                                  maxnoimprovments=MAX_NO_IMPROVEMENTS,
                                  stats=stats, halloffame=hof, verbose=True)

# pop, logbook = deap.algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=MAX_GENERATIONS,
#                                   stats=stats, halloffame=hof, verbose=True)

if CSV_FILE is not None:
    with open(CSV_FILE, 'w+') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=logbook.header)
        writer.writeheader()
        writer.writerows(logbook[0:len(logbook)])
        csvfile.close()

print(hof)
print(hof[0].fitness.valid)
print("Best fitness: {}".format(hof[0].fitness))

solution = helper.individual_to_solution(hof[0])
table = solution.get_as_table(problem, begin_with_1=True)
# Print result and save them to file
print(table)
table.to_csv(PLAN_CSV_FILE)
