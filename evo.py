""" Evolutionary solver for shift planning in UKE

Created during Hackaton WirvsVirus

Author: Ruslan Krenzler, 2020

This code is under the public domain licence CC0, See https://creativecommons.org/


23. March 2020
"""

from problem import FREE, EARLY_SHIFT, LATE_SHIFT, NIGHT_SHIFT, Solution
import numpy as np


# Every complete solution is a sequence of personal plans.
# Every personal plan is a sequence of [DAYS]-numbers of numbers 0,1,2,3. That is 3,3,1,2,2,0...

# The fitness of the individual is a number of not used capacities for per day.
# Assume the CAPACITY is 6. That means if there are two days in the whole plan with 5 employees and in all other days
# have 6 employees. The fitness is -2.
# Overusing of the capacity is also penalized with -1. That is if a plan contains 7 employees it will decrease
# the fitness function by -1.

# The system must fulfill constrains. If one of them is violated the cost function is then
# the same as for all unused capacities + 1. This assures that any such a solution is worse than a plan
# where nobody works.


# This class helps to create initial solutions and evaluation populations
class Helper:
    def __init__(self, problem):
        """Initialize helper class with a system and and place order."""
        self.problem = problem
        self.costs_for_unused_capacity = 1.0
        self.costs_for_wasted_capacity = 1.0
        self.infeasible_costs = Helper._all_unused_capcities_costs(problem, self.costs_for_unused_capacity) + 1.0
        self.ndays = len(problem.demand)  # Number of days in the plan.
        self.nemployees = problem.nemployees

    @staticmethod
    def _all_unused_capcities_costs(problem, cost_per_capacity):
        """Calculate costs if no capacity is used."""
        total_demand = 0
        for daily_demand in problem.demand:
            total_demand += daily_demand.e + daily_demand.l + daily_demand.n
        return total_demand * cost_per_capacity

    def individual_size(self):
        return self.nemployees * self.ndays

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
                if i < (len(subplan) - 2):
                    if subplan[i + 1] != NIGHT_SHIFT and (subplan[i + 1] != FREE and subplan[i + 2] != FREE):
                        return False
                # TODO: We need to discuss, how this constraint work on the day before the last day.
                # I assume it is sufficient to have only one free day too.
                else:
                    if subplan[i + 1] != NIGHT_SHIFT and (subplan[i + 1] != FREE):
                        return False
        return True

    @staticmethod
    def shift_type_4(subplan, start_index):
        """ Nach 4 geleisteten Schichten hat der MA minimum einen Tage frei.

        TODO: It is not clear, what to do for the days after the plan ends.
        To make it easy we assume tha the following days are.
        """
        in_a_row = 0
        free_days = 0
        if start_index + 4 >= len(subplan):
            return True  # Plan ends, we assume there will be a free days later.
        else:
            if subplan[start_index + 4] != FREE:
                free_days += 1

        for i in range(0, start_index + 4):
            if subplan[i] != FREE:
                in_a_row += 1
            else:
                in_a_row = 0  # Reset counter.

        if in_a_row == 4 and free_days == 1:
            return False

        return True

    @staticmethod
    def shift_type_8(subplan, start_index):
        """ Nach 8 geleisteten Schichten hat der MA minimum zwei Tage frei.

        TODO: It is not clear, what to do for the days after the plan ends.
        To make it easy we assume tha the following days are.
        """
        in_a_row = 0
        free_days = 0
        if start_index + 8 >= len(subplan):
            return True  # Plan ends, we assume there will be free days after.
        if start_index + 8 == len(subplan):
            free_days = 2  # After 8 days the plan ends. We do not know if the employee will have a free day,
            # but we assume that it is free to keep it simple.
        elif start_index + 8 == len(subplan) -1 :
            free_days = 1  # After 9 days the plan ends. We do not know if the employee will have a free day,
            # but we assume that it is free to keep it simple.
        else:
            if  subplan[start_index + 8] != FREE:
                free_days += 1
            if subplan[start_index + 8 + 1] != FREE:
                free_days += 1

        for i in range(0, start_index + 8):
            if subplan[i] != FREE:
                in_a_row += 1
            else:
                in_a_row = 0  # Reset counter.

        if in_a_row == 8 and free_days == 2:
            return False

        return True

    @staticmethod
    def shift_type_4_or_8(subplan):
        """For every day, either the rule for 4 or the rule for 8 consecutive days must apply.
        """
        for i in range(0, len(subplan) - 4):
            if Helper.shift_type_4(subplan, i) == False and Helper.shift_type_8(subplan, i) == False:
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
            else:
                in_a_row = 0  # Reset counter.
            if in_a_row == 10 and subplan[i + 1]:
                return False

        return True

    @staticmethod
    def shift_worked(subplan, start_index, end_index):
        """Calculate number of worked shifts in days [start_index, end_index)."""
        res = 0
        for i in range(start_index, end_index):
            if subplan[i] != FREE:
                res += 1
        return res

    @staticmethod
    def shift_type_14(subplan):
        """ In 14 Tagen arbeitet der Mitarbeiter maximal 10 Schichten.

        This is not optimized version.
        """
        for begin_i in range(0, len(subplan) - 14):
            w = Helper.shift_worked(subplan, begin_i, begin_i + 14)
            if w > 10:
                return False

        return True

    def evaluate(self, individual) -> float:
        """Return average costs of the system solved with information in individual.

        :param individual: sequence of sequences
        """
        # split whole plan in employee plans.
        personal_plans = np.array_split(individual, self.nemployees)
        costs = 0.0
        # Add huge costs (more than if no one works) for each violated rule per person.
        for personal_plan in personal_plans:
            if not Helper.nex_day_constraint(personal_plan):
                costs += self.infeasible_costs
                continue
            if not Helper.shift_type_4_or_8(personal_plan) and not Helper.shift_type_8(personal_plan):
                costs += self.infeasible_costs
                continue
            if not Helper.shift_type_14(personal_plan):
                costs += self.infeasible_costs
                continue

        # Check if we used all the capacity
        used_capacities_early = [0] * self.ndays
        used_capacities_late = [0] * self.ndays
        used_capacities_night = [0] * self.ndays
        for personal_plan in personal_plans:
            for day_index in range(0, len(personal_plan)):
                if personal_plan[day_index] == EARLY_SHIFT:
                    used_capacities_early[day_index] += 1
                elif personal_plan[day_index] == LATE_SHIFT:
                    used_capacities_late[day_index] += 1
                elif personal_plan[day_index] == NIGHT_SHIFT:
                    used_capacities_night[day_index] += 1
        # Add costs costs for unused and wasted capacities
        for day, cap in enumerate(used_capacities_early):
            costs += max(self.problem.demand[day].e - cap, 0) * self.costs_for_unused_capacity
            costs += max(cap - self.problem.demand[day].e, 0) * self.costs_for_wasted_capacity
        for day, cap in enumerate(used_capacities_late):
            costs += max(self.problem.demand[day].l - cap, 0) * self.costs_for_unused_capacity
            costs += max(cap - self.problem.demand[day].l, 0) * self.costs_for_wasted_capacity
        for day, cap in enumerate(used_capacities_night):
            costs += max(self.problem.demand[day].n - cap, 0) * self.costs_for_unused_capacity
            costs += max(cap - self.problem.demand[day].l, 0) * self.costs_for_wasted_capacity

        costs = (costs,)
        return costs

    def individual_to_solution(self, individual):
        solution = Solution()
        solution.personal_plans = np.array_split(individual, self.nemployees)
        return solution
