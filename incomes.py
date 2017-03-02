"""This module contains classes for various types of incomes"""

import collections
import math
import random
import world
import utils
import funds

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
      current_ympe = utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE) * year_rec.cpi
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
      self.ympe_fractions.append(year_rec.pensionable_earnings / (utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE) * year_rec.cpi))

  def OnRetirement(self, person):
    self.ympe_fractions.sort(reverse=True)
    working_years = len(self.ympe_fractions)
    dropout_years = world.CPP_GENERAL_DROPOUT_FACTOR * working_years
    cpp_earning_history_length = working_years - dropout_years
    whole_year_index = math.floor(cpp_earning_history_length)
    cpp_average_earnings = (sum(self.ympe_fractions[:whole_year_index]) +
                            self.ympe_fractions[whole_year_index]*(cpp_earning_history_length - whole_year_index)) / cpp_earning_history_length

    # Calculate the average nominal YMPE for the previous 5 years (excluding current year)
    nominal_ympe_history = [utils.Indexed(world.YMPE, person.year - i, 1 + world.PARGE) * person.cpi_history[-(i+1)]
                            for i in range(1, world.MPEA_YEARS + 1)]
    indexed_mpea = sum(nominal_ympe_history)/world.MPEA_YEARS

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
    self.last_year_cpi = 1

  def CalcAmount(self, year_rec):
    if year_rec.age >= world.CPP_EXPECTED_RETIREMENT_AGE:
      return world.OAS_BENEFIT * self.last_year_cpi
    else:
      return 0

  def AnnualUpdate(self, year_rec):
    self.last_year_cpi = year_rec.cpi


class GIS(Income):
  
  def __init__(self):
    self.taxable = False
    self.income_type = INCOME_TYPE_GIS
    self.last_year_income_base = 0

  def _CalcIncomeBase(self, year_rec):
    rrsp_withdrawal_sum = sum(receipt.amount for receipt in year_rec.withdrawals
                              if receipt.fund_type in (funds.FUND_TYPE_RRSP, funds.FUND_TYPE_BRIDGING))
    taxable_capital_gains = (sum(receipt.gains for receipt in year_rec.withdrawals) +
                             sum(receipt.gross_gain for receipt in year_rec.tax_receipts)) * world.CG_INCLUSION_RATE
    income_base = (sum(receipt.amount for receipt in year_rec.incomes
                      if receipt.income_type in (INCOME_TYPE_EARNINGS, INCOME_TYPE_CPP, INCOME_TYPE_EI))
                   + rrsp_withdrawal_sum + taxable_capital_gains - year_rec.ei_premium - year_rec.cpp_contribution)
    gis_income = min(income_base, self.last_year_income_base)
    self.last_year_income_base = income_base
    return gis_income

  def CalcAmount(self, year_rec):
    gis_income = self._CalcIncomeBase(year_rec)
    if sum(receipt.amount for receipt in year_rec.incomes if receipt.income_type == INCOME_TYPE_OAS) > 0:
      gis_benefit = max(world.GIS_SINGLES_RATE * year_rec.cpi - max(gis_income - world.GIS_CLAWBACK_EXEMPTION, 0) * world.GIS_REDUCTION_RATE, 0)
      gis_supplement = max(world.GIS_SUPPLEMENT_MAXIMUM * year_rec.cpi - max(gis_income - world.GIS_SUPPLEMENT_EXEMPTION * year_rec.cpi, 0) * world.GIS_SUPPLEMENT_REDUCTION_RATE, 0)
      return gis_benefit + gis_supplement
    else:
      return 0
