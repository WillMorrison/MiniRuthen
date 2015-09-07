"""This module contains classes for various types of incomes"""

import collections
import math
import random
import world
import utils

# Types of incomes, used in receipts
INCOME_TYPE_NONE = "Generic Income"
INCOME_TYPE_EARNINGS = "Earnings"
INCOME_TYPE_EI = "EI"
INCOME_TYPE_CPP = "CPP"
INCOME_TYPE_OAS = "OAS"
INCOME_TYPE_GIS = "GIS"

# Receipts go into year records
IncomeReceipt = collections.namedtuple('IncomeReceipt', ('amount', 'income_type'))

class Income(object):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_NONE

  def GiveMeMoney(self, year_rec):
    """Called each year with a partially completed YearRecord"""
    amount = self.CalcAmount(year_rec)
    year_rec.incomes.append(IncomeReceipt(amount, self.income_type))
    return (amount, self.taxable, year_rec)

  def AnnualUpdate(self, year_rec):
    """Called at the end of each year with that year's YearRecord"""
    pass

  def CalcAmount(self, year_rec):
    """Calculates the amount to be paid"""
    return 0

  def OnRetirement(self, person):
    """Called to indicate that retirement has just happened"""
    pass


class Earnings(Income):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_EARNINGS

  def CalcAmount(self, year_rec):
    if year_rec.is_employed:
      current_ympe = utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE) 
      earnings = max(random.normalvariate(current_ympe * world.EARNINGS_YMPE_FRACTION, world.YMPE_STDDEV * current_ympe), 0)
      return earnings
    else:
      return 0

class EI(Income):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_EI
    self.was_employed_last_year = True
    self.last_year_insurable_earnings = world.EI_PREINITIAL_YEAR_INSURABLE_EARNINGS

  def CalcAmount(self, year_rec):
    if not year_rec.is_employed and self.was_employed_last_year and not year_rec.is_retired:
      return self.last_year_insurable_earnings * world.EI_BENEFIT_FRACTION
    else:
      return 0

  def AnnualUpdate(self, year_rec):
    self.was_employed_last_year = year_rec.is_employed
    self.last_year_insurable_earnings = year_rec.insurable_earnings


class CPP(Income):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_CPP
    self.benefit_amount = 0
    self.ympe_fractions = world.PRE_SIM_YMPE_FRACTIONS[:]

  def CalcAmount(self, year_rec):
    return self.benefit_amount

  def AnnualUpdate(self, year_rec):
    if not year_rec.is_retired:
      self.ympe_fractions.append(year_rec.pensionable_earnings / utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE))

  def OnRetirement(self, person):
    cpp_avg_earnings = 0
    self.ympe_fractions.sort(reverse=True)
    working_years = len(self.ympe_fractions)
    dropout_years = world.CPP_GENERAL_DROPOUT_FACTOR * working_years
    cpp_earning_history_length = working_years - dropout_years
    whole_year_index = math.floor(cpp_earning_history_length)
    cpp_average_earnings = sum(self.ympe_fractions[:whole_year_index]) + self.ympe_fractions[whole_year_index]*(cpp_earning_history_length - whole_year_index)
    indexed_mpea = utils.Indexed(world.MPEA, person.age - world.START_AGE + world.BASE_YEAR, 1 + world.PARGE)

    if person.age == world.CPP_EXPECTED_RETIREMENT_AGE:
      self.benefit_amount = cpp_average_earnings * indexed_mpea * world.CPP_RETIREMENT_BENEFIT_FRACTION
    elif person.age < world.CPP_EXPECTED_RETIREMENT_AGE:
      self.benefit_amount = (cpp_average_earnings * indexed_mpea * world.CPP_RETIREMENT_BENEFIT_FRACTION *
                             (1 - (world.CPP_EXPECTED_RETIREMENT_AGE - person.age)*world.AAF_PRE65))
    elif person.age > world.CPP_EXPECTED_RETIREMENT_AGE:
      self.benefit_amount = (cpp_average_earnings * indexed_mpea * world.CPP_RETIREMENT_BENEFIT_FRACTION *
                             (1 + min(world.AAF_POST65_YEARS_CAP, person.age - world.CPP_EXPECTED_RETIREMENT_AGE) * world.AAF_POST65))

class OAS(Income):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_OAS


class GIS(Income):
  
  def __init__(self):
    self.taxable = False
    self.income_type = INCOME_TYPE_GIS
