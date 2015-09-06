"""This module contains classes for various types of incomes"""

import collections
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
    amount = self.CalcAmount(year_rec)
    year_rec.incomes.append(IncomeReceipt(amount, self.income_type))
    return (amount, self.taxable, year_rec)

  def AnnualUpdate(self, year_rec):
    pass

  def CalcAmount(self, year_rec):
    """Calculates the amount to be paid"""
    return 0


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
      0

  def AnnualUpdate(self, year_rec):
    self.was_employed_last_year = year_rec.is_employed
    self.last_year_insurable_earnings = year_rec.insurable_earnings


class CPP(Income):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_CPP


class OAS(Income):
  
  def __init__(self):
    self.taxable = True
    self.income_type = INCOME_TYPE_OAS


class GIS(Income):
  
  def __init__(self):
    self.taxable = False
    self.income_type = INCOME_TYPE_GIS
