""" Evolutionary solver for shift planning in UKE

Created during Hackaton WirvsVirus

Author: Ruslan Krenzler, 2020

This code is under the public domain licence CC0, See https://creativecommons.org/


23. March 2020
"""
from collections import namedtuple
import numpy as np
import pandas as pd

SHIFTS_PER_DAY = 3  # Number of shifts per day
FREE = 0
EARLY_SHIFT = 1
LATE_SHIFT = 2
NIGHT_SHIFT = 3
INVALID_INDEX = -1

"""This class stores how many shifts one need in a day."""
DailyDemand = namedtuple('DailyDemand', ['e', 'l', 'n'], verbose=False)


class Problem:
    """This class describes optimization problem

    It contains daily demands and number of available employees.
    """

    def __init__(self):
        # Set default values
        self.nemployees = 0  # Under default settings, we have no employees.
        self.demand = []  # Under default settings, we do not have any demand.


class ProblemBuilder:
    """ Build a test problem where we have 40 Employees, and 30 days of plan
    # And we need 6 people to work in parallel. """

    @staticmethod
    def generate(nemp: int, ndays: int, npar: int) -> Problem:
        """Generate problem for a constant demand of parallel employees for all three type of shifts

        Parameters
        ----------
        nemp: int
            Total number of employees in the system.
        ndays: int
            Total number of days in the plan.
        npar: int
            Total number of employees who must work in parallel.

        Returns
        -------
        Problem

        For example nemp=40,ndays=30,npar=6 will generate a problem where there is 40 employees
        and they need to work for 30 days and during each shift 6 employees must work in parallel.
        """
        problem = Problem()
        problem.nemployees = nemp
        # Add demand
        for day in range(0, ndays):
            problem.demand.append(DailyDemand(npar, npar, npar))
        return problem


class Solution:
    """The solution describes day and shift for every employee.

    The employees are represented with number 0,1,2,...
    The days are represented with numbers 0,1,2,3,...
    """

    def __init__(self):
        """Init solution."""

        # Personal plan is a list of lists.
        # The element [i][d] means, shift of the employee i for day d.
        # The personal list must have the same size.
        self.personal_plans = []

    def __str__(self):
        """Return a plans"""

    def _get_shift_plan(self, shift_type: int):
        """ Return plan for a particular shift.

        Parameters
        ----------
        shift_type: int
            Type of the shift. It can be EARLY_SHIFT, LATE_SHIFT or NIGHT_SHIFT.

        Returns
        -------
        list of lists
            where every element [d] is  a list of Employees for this day
            and this type of shift.

        """
        if not self.personal_plans:
            return []  # Empty plan, nothing to do.

        # The personal plans must have the same size. Get number of days from 0-th plan.
        ndays = len(self.personal_plans[0])

        result = [[] for i in range(ndays)]
        for pi, plan in enumerate(self.personal_plans):
            for di, day in enumerate(plan):
                if plan[di] == shift_type:
                    result[di].append(pi)
        # In order to make results easy to read sort employee indices for very day.
        for di, day in enumerate(result):
            result[di] = list(sorted(day))
        return result

    @staticmethod
    def _get_max_employee_per_shift(plan: list):
        """Return maximal number of person for a particular shift type in the whole plan.

        Parameters
        ----------
        plan: list of lists
            List of daily plans for a particular type of shift
        """
        n = 0
        for day in plan:
            n = max(n, len(day))
        return n

    def _get_as_table(self, shift_type: int, shift_name, problem, begin_with_1):
        """ Return plan for a particular shift as a panda table.

        if prefix is not none, the 0-column will contain the shift type.
        The 0-column with name "ShiftType" contains shift type, the i-column contains the
        The other columns have names "Day0", "Day1", "Day2", and so on, they contain
        an index of an employee. -1 means that there is no employee.

        If you wand to name the days "Day1", "Day2", "Day3",.... and
        employees 1,2,3,...0 and invalid employee -1, set begin_with_1 to True

        """
        if not self.personal_plans:
            return pd.DataFrame()  # Empty plan, nothing to do.

        shift_plan = self._get_shift_plan(shift_type)
        nrows = Solution._get_max_employee_per_shift(shift_plan)
        # Add rows for missing demands, if maximal number of employees per day in the solution
        # is smaller as the demand on that day. This is done to emphisize missing employees
        if problem is not None:
            nrows = max(nrows, Solution._max_demand(problem.demand, shift_type))

        ncols = len(self.personal_plans[0])
        base = 0
        if begin_with_1 == True:
            base = 1

        colnames = ["Day{}".format(ri+base) for ri in range(ncols)]
        table = pd.DataFrame(np.full(shape=(nrows, ncols), fill_value=(INVALID_INDEX+base)), columns=colnames)
        # Fill the table column-wisely.
        for di, day_plan in enumerate(shift_plan):
            for ei, employee in enumerate(day_plan):
                table["Day{}".format(di+base)][ei] = employee + base

        # if shift_type is set, add the very first column with that shift type.
        if shift_name is not None:
            # TODO this does not work as expected. If you change one element of the column
            # all the elements will be changed.
            col = pd.DataFrame([shift_name for i in range(nrows)])
            table = pd.concat([col, table], axis=1)
        return table

    @staticmethod
    def _max_demand(demand: list, shift_type: int):
        e = 0; l = 0; n = 0
        for daily in demand:
            e = max(e, daily.e)
            l = max(l, daily.l)
            n = max(n, daily.n)

        if shift_type == EARLY_SHIFT:
            return e
        elif shift_type == LATE_SHIFT:
            return l
        elif shift_type == NIGHT_SHIFT:
            return n

    def get_as_table(self, problem = None, begin_with_1=False):
        """ Return solution as a table with columns "ShiftType", "Day0", "Day1", "Day2", ....

        Parameters
        ----------
        problem: Problem
            problem helps to determine unused capacity of the solution.
        """
        tables = [self._get_as_table(EARLY_SHIFT, "Early", problem, begin_with_1),
                  self._get_as_table(LATE_SHIFT, "Late", problem, begin_with_1),
                  self._get_as_table(NIGHT_SHIFT, "Night", problem, begin_with_1)]
        table = pd.concat(tables, axis=0)
        table = table.reset_index(drop=True)
        return table
