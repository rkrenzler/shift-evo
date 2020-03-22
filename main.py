# Optimize shifts for medical staff.
# Ruslan Krenzler 21.03.2020
# The code is under LGPL.
# This code is ugly. It is only proof of concept.

import copy
import pickle
import random  # For seed.
import array
import csv
import multiprocessing

import numpy
import deap
from deap import base
from deap import creator
from deap import tools
import deap.algorithms

# Use normal random instead of numpy.random.seed(7) to get reproducible results.
random.seed(7)

EMPLOYEES = 40  # Number of available employers
# EMPLOYEES = 12 # Number of available employers
DAYS = 30  # Number of days.
# DAYS = 4 # Number of days.
SHIFTS_PER_DAY = 3  # Number of
FREE = 0
EARLY_SHIFT = 1
LATE_SHIFT = 2
NIGHT_SHIFT = 3

CAPACITY = 6  # How many employees should work in parallel.

PLAN_CSV_FILE = 'plan.csv'  # Here we store the resulting file.

# Every complete solution is a sequence of EMLOYEES-number of personal plans.
# Every personal plan is a sequence of [DAYS]-numbers of numbers 0,1,2,3. That is 3,3,1,2,2,0...

# The fitness of the individual is a number of not used capacities for per day.
# Assume the CAPACITY is 6. That means if there are two days in the whole plan with 5 employees and in all other days
# have 6 employees. The fitness is -2.
# Overusing of the capacity is also penalized with -1. That is if a plan contains 7 employees it will decrease
# the fitness function by -1.

# The system must fulfill constrains. If one of them is violated the fitness function is then
# - CAPACITY*SHIFTS_PER_DAY*DAYS - 1. This assures that any such a solution is worse than a plan
# where nobody works. Such a plan has a fitness function -CAPACITY*SHIFTS_PER_DAY*DAYS


# This class helps to create initial solutions and evaluation populations
class Helper:
    def __init__(self):
        """Initialize helper class with a system and and place order."""
        self.costs_for_unused_capacity = 1.0
        self.costs_for_wasted_capacity = 1.0
        self.infeasible_costs = SHIFTS_PER_DAY * CAPACITY * DAYS * self.costs_for_unused_capacity + 1

    @staticmethod
    def individual_size():
        return EMPLOYEES * DAYS

    def no_one_works(self):
        return [FREE] * self.individual_size()

    @staticmethod
    def min_decision():
        return FREE

    @staticmethod
    def max_decision():
        return NIGHT_SHIFT

    @staticmethod
    def nex_day_constraint(subplan):
        """ Check that the personal plan fullfill constraints for the next day.

        :params personal plan of one employee.
        :returns True if condition is fulfilled, and False otherwise
        """
        for i in range(0, len(subplan) - 1):
            #  Auf einen Frühdienst folgt am nächsten Tag nur ein weiterer Frühdienst, ein Spätdienst oder ein Freier
            #  Tag, aber kein Nachtdienst
            if subplan[i] == EARLY_SHIFT:
                if subplan[i + 1] == NIGHT_SHIFT:
                    return False
            #  Auf einen Spätdienst folgt am nächsten Tag nur ein weiterer Spätdienst, ein Nachtdienst oder ein freier
            #  Tag, aber kein Frühdienst
            elif subplan[i] == LATE_SHIFT:
                if subplan[i + 1] == EARLY_SHIFT:
                    return False
            # Auf einen Nachtdienst folgt am nächsten Tag nur ein weiterer Nachtdienst oder zwei freie Tage
            elif subplan[i] == NIGHT_SHIFT:
#                pass
                if i < (len(subplan) - 2):
                    if subplan[i + 1] != NIGHT_SHIFT and (subplan[i + 1] != FREE and subplan[i + 2] != FREE):
                        return False
                # TODO: We need to discuss, how this constraint work on the day before the last day.
                else:
                    if subplan[i + 1] != NIGHT_SHIFT:
                        return False
        return True

    @staticmethod
    def shift_type_4(subplan):
        """ Nach 4 geleisteten Schichten hat der MA minimum einen Tag frei."""
        in_a_row = 0
        for i in range(0, len(subplan) - 1):
            if subplan[i] != FREE:
                in_a_row += 1

            if in_a_row == 4 and subplan[i + 1] != FREE:
                return False
        return True

    @staticmethod
    def shift_type_8(subplan):
        """ Nach 8 geleisteten Schichten hat der MA minimum zwei Tage frei"""
        in_a_row = 0
        for i in range(0, len(subplan) - 2):
            if subplan[i] != FREE:
                in_a_row += 1

            if in_a_row == 8 and (subplan[i + 1] != FREE or subplan[i + 2] != FREE):
                return False
        return True

    @staticmethod
    def shift_type_10(subplan):
        """  Es werden maximal 10 Schichten am Stück geplant, danach geht ein Mitarbeiter ins frei

        Remark: This rule does not make any sence, since it follows from the rule shift_type_14.
        """
        in_a_row = 0
        for i in range(0, len(subplan) - 1):
            if subplan[i] != FREE:
                in_a_row += 1

            if in_a_row == 10 and subplan[i + 1]:
                return False
        return True

    @staticmethod
    def shift_type_14(subplan):
        """ In 14 Tagen arbeitet der Mitarbeiter maximal 10 Schichten.
        TODO:
        """
        return True

    def evaluate(self, individual) -> float:
        """Return average costs of the system solved with information in individual.

        :param individual: sequence of sequences
        """
        # split whole plan in employee plans.
        personal_plans = numpy.array_split(individual, EMPLOYEES)
        costs = 0.0
        for personal_plan in personal_plans:
            if not Helper.nex_day_constraint(personal_plan):
                costs = self.infeasible_costs + 1
                #                print("return costs {}".format(costs))
                break
            if not Helper.shift_type_4(personal_plan) and not Helper.shift_type_8(personal_plan):
                costs = self.infeasible_costs + 2
                #                print("return costs {}".format(costs))
                break
            if not Helper.shift_type_14(personal_plan):
                costs = self.infeasible_costs + 3
                #                print("return costs {}".format(costs))
                break

        # Check if we used all the capacity
        used_capacities_early = [0] * DAYS
        used_capacities_late = [0] * DAYS
        used_capacities_night = [0] * DAYS
        for personal_plan in personal_plans:
            for day_index in range(0, len(personal_plan)):
                if personal_plan[day_index] == EARLY_SHIFT:
                    used_capacities_early[day_index] += 1
                elif personal_plan[day_index] == LATE_SHIFT:
                    used_capacities_late[day_index] += 1
                elif personal_plan[day_index] == NIGHT_SHIFT:
                    used_capacities_night[day_index] += 1
        # Calculate costs for unused and wasted capacities
        # costs = 0.0
        for cap in used_capacities_early:
            costs += max(CAPACITY - cap, 0) * self.costs_for_unused_capacity
            costs += max(cap - CAPACITY, 0) * self.costs_for_wasted_capacity
        for cap in used_capacities_late:
            costs += max(CAPACITY - cap, 0) * self.costs_for_unused_capacity
            costs += max(cap - CAPACITY, 0) * self.costs_for_wasted_capacity
        for cap in used_capacities_night:
            costs += max(CAPACITY - cap, 0) * self.costs_for_unused_capacity
            costs += max(cap - CAPACITY, 0) * self.costs_for_wasted_capacity

        costs = (costs,)
        #        print("return costs {}".format(costs))
        return costs


#    """Create a random feasible individual.
#    TODO: """
#    def random_solution(self):
#        pass

def min_fitness(population):
    """Determine minimal fitness of populataion.

    The population is a list of individuals"""
    ret_val = float("inf")
    for ind in population:
        if ind.fitness.values[0] < ret_val:
            ret_val = ind.fitness.values[0]

    return ret_val


def shift_to_row(prefix, shift):
    nrows = CAPACITY
    ncols = len(shift)
    for day_plan in shift:
        nrows = max(nrows, len(day_plan))

    table = numpy.full((nrows, 1 + ncols), "  ", dtype=object, order='C')

    # The 0 column contain prefixs
    for i in range(0, nrows):
        table[i, 0] = prefix

    # Add employees.

    for day_index in range(0, len(shift)):
        day_plan = shift[day_index]
        row_index = 0
        for id in day_plan:
            # The index 0 is reserved for prefix.
            table[row_index, day_index + 1] = "M{:02d}".format(id)
            row_index += 1
    return table


def individual_to_plan(individual):
    early_shifts = [[] for i in range(DAYS)]  # Do not use [[]]*DAYS! It will create list with the same list object.
    late_shifts = [[] for i in range(DAYS)]
    night_shifts = [[] for i in range(DAYS)]
    personal_plans = numpy.array_split(individual, EMPLOYEES)
    person_id = 1
    for personal_plan in personal_plans:
        for i in range(0, len(personal_plan)):
            if personal_plan[i] == EARLY_SHIFT:
                late_shifts[i].append(person_id)
            elif personal_plan[i] == LATE_SHIFT:
                early_shifts[i].append(person_id)
            elif personal_plan[i] == NIGHT_SHIFT:
                night_shifts[i].append(person_id)

        person_id += 1
    t1 = shift_to_row("Frühschicht:  ", early_shifts)
    t2 = shift_to_row("Spätschicht:  ", late_shifts)
    t3 = shift_to_row("Nachtschicht: ", night_shifts)
    t = numpy.concatenate((t1, t2, t3), axis=0)
    return t


# This is modified version of deap.algorithm.eaSimple. The only modification is additional stopping
# criteria. Maximal number of generation without improvment. maxnoimprovment
def eaSimpleCustomized(population, toolbox, cxpb, mutpb, ngen, maxnoimprovments=None, stats=None,
                       halloffame=None, verbose=__debug__, checkpoint_prefix=None, checkpoint_frequency=100,
                       results_csv=None):
    """This algorithm reproduce the simplest evolutionary algorithm as
    presented in chapter 7 of [Back2000]_.

    :param population: A list of individuals.
    :param toolbox: A :class:`~deap.base.Toolbox` that contains the evolution
                    operators.
    :param cxpb: The probability of mating two individuals.
    :param mutpb: The probability of mutating an individual.
    :param ngen: The number of generation.
    :param maxnoimprovments: Stopping criterial. The algorithm stops if there was no imrovement in the last
        maxnoimprovment generations.
    :param stats: A :class:`~deap.tools.Statistics` object that is updated
                  inplace, optional.
    :param halloffame: A :class:`~deap.tools.HallOfFame` object that will
                       contain the best individuals, optional.
    :param verbose: Whether or not to log the statistics.
    :returns: The final population
    :returns: A class:`~deap.tools.Logbook` with the statistics of the
              evolution

    The algorithm takes in a population and evolves it in place using the
    :meth:`varAnd` method. It returns the optimized population and a
    :class:`~deap.tools.Logbook` with the statistics of the evolution. The
    logbook will contain the generation number, the number of evalutions for
    each generation and the statistics if a :class:`~deap.tools.Statistics` is
    given as argument. The *cxpb* and *mutpb* arguments are passed to the
    :func:`varAnd` function. The pseudocode goes as follow ::

        evaluate(population)
        for g in range(ngen):
            population = select(population, len(population))
            offspring = varAnd(population, toolbox, cxpb, mutpb)
            evaluate(offspring)
            population = offspring

    As stated in the pseudocode above, the algorithm goes as follow. First, it
    evaluates the individuals with an invalid fitness. Second, it enters the
    generational loop where the selection procedure is applied to entirely
    replace the parental population. The 1:1 replacement ratio of this
    algorithm **requires** the selection procedure to be stochastic and to
    select multiple times the same individual, for example,
    :func:`~deap.tools.selTournament` and :func:`~deap.tools.selRoulette`.
    Third, it applies the :func:`varAnd` function to produce the next
    generation population. Fourth, it evaluates the new individuals and
    compute the statistics on this population. Finally, when *ngen*
    generations are done, the algorithm returns a tuple with the final
    population and a :class:`~deap.tools.Logbook` of the evolution.

    .. note::

        Using a non-stochastic selection method will result in no selection as
        the operator selects *n* individuals from a pool of *n*.

    This function expects the :meth:`toolbox.mate`, :meth:`toolbox.mutate`,
    :meth:`toolbox.select` and :meth:`toolbox.evaluate` aliases to be
    registered in the toolbox.

    .. [Back2000] Back, Fogel and Michalewicz, "Evolutionary Computation 1 :
       Basic Algorithms and Operators", 2000.
    """
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])
    # If results_csv is set save csv files.
    csv_writer = None
    if results_csv is not None:
        import csv
        csvfile = open(results_csv, 'w+')
        csv_writer = csv.DictWriter(csvfile, fieldnames=logbook.header)
        csv_writer.writeheader()

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in population if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    if halloffame is not None:
        halloffame.update(population)

    record = stats.compile(population) if stats else {}
    logbook.record(gen=0, nevals=len(invalid_ind), **record)
    if verbose:
        print(logbook.stream)

    if maxnoimprovments is None:
        maxnoimprovments = ngen + 1
    noimprovements = 0
    best_fitness_so_far = min_fitness(population)

    # Begin the generational process
    for gen in range(1, ngen + 1):
        # Select the next generation individuals
        offspring = toolbox.select(population, len(population))

        # Vary the pool of individuals
        offspring = deap.algorithms.varAnd(offspring, toolbox, cxpb, mutpb)

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Update the hall of fame with the generated individuals
        if halloffame is not None:
            halloffame.update(offspring)

        # Replace the current population by the offspring
        population[:] = offspring

        # Append the current generation statistics to the logbook
        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        if verbose:
            print(logbook.stream)
        if csv_writer is not None:
            csv_writer.writerow(logbook[-1])
            csvfile.flush()
        # Check if this generation has some improvements.
        generation_fitnes = min_fitness(population)
        if generation_fitnes < best_fitness_so_far:
            best_fitness_so_far = generation_fitnes
            noimprovements = 0
        else:
            noimprovements += 1

        if checkpoint_prefix is not None:
            if gen % checkpoint_frequency == 0:
                # Fill the dictionary using the dict(key=value[, ...]) constructor
                cp = dict(population=population, generation=gen, halloffame=halloffame,
                          logbook=logbook, rndstate=random.getstate())

                filename = checkpoint_prefix + "-gen-{}.pkl".format(gen)
                with open(filename, "wb") as cp_file:
                    pickle.dump(cp, cp_file)

        if noimprovements >= maxnoimprovments:
            if verbose:
                print("Maximal number of not improved genrations {} reached.".format(maxnoimprovments))
            break

    return population, logbook


POPULATION_SIZE = 100
MAX_GENERATIONS = 10000
MAX_NO_IMPROVEMENTS = 1000
# Set it to None if you do not want to write data to a file.
CSV_FILE = None

helper = Helper()
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
pop, logbook = eaSimpleCustomized(pop, toolbox, cxpb=0.5, mutpb=0.02, ngen=MAX_GENERATIONS,
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

t = individual_to_plan(hof[0])
print(t)
# Save to csv and print
# numpy.savetxt("plan.csv", t, delimiter=",") # This does not work.

with open(PLAN_CSV_FILE, 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
    nrows = numpy.size(t, axis=0)
    for r in range(0, nrows):
        row = list(t[r, :])
        writer.writerow(row)

