

""" Evolutionary solver for shift planning in UKE

Created during Hackaton WirvsVirus

Author: Ruslan Krenzler, 2020

This code is under the public domain licence CC0, See https://creativecommons.org/


23. March 2019
"""
from _collections import namedtuple

SHIFTS_PER_DAY = 3  # Number of shifts per day
FREE = 0
EARLY_SHIFT = 1
LATE_SHIFT = 2
NIGHT_SHIFT = 3

"""This class stores how many shifts one need in a day."""
DailyDemand = namedtuple('DailyDemand', ['e', 'l', 'n'], verbose=False)


class Problem:
    """This class describes optimization problem

    It contains daily demands and number of available employees.
    """
    def __init__(self):
        # Set default values
        self.nemployees = 0  # Under default settings, we have no employees.
        self.demand = []  #  Under default settings, we do not have any demand.


class ProblemBuilder:
    """ Build a test problem where we have 40 Employees, and 30 days of plan
    # And we need 6 people to work in parallel. """
    @staticmethod
    def generate(nemp: int, ndays: int, npar: int)->Problem:
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






