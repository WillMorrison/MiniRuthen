import collections
import random
import funds
import utils
import world

MALE = "m"
FEMALE = "f"

Strategy = collections.namedtuple("Strategy",
                                  ["planned_retirement_age",
                                   "savings_threshold",
                                   "savings_rate",
                                   "savings_rrsp_fraction",
                                   "savings_tfsa_fraction",
                                   "lico_target_fraction",
                                   "working_period_drawdown_tfsa_fraction",
                                   "working_period_drawdown_nonreg_fraction",
                                   "oas_bridging_fraction",
                                   "drawdown_ced_fraction",
                                   "initial_cd_fraction",
                                   "drawdown_preferred_rrsp_fraction",
                                   "drawdown_preferred_tfsa_fraction",
                                   "reinvestment_preference_tfsa_fraction",])

class Person(object):
  
  def __init__(self, strategy, gender=FEMALE):
    self.year = world.BASE_YEAR
    self.age = world.START_AGE
    self.gender = gender
    self.strategy = strategy
    self.employed_last_year = True
    self.retired = False
    self.incomes = [incomes.Earnings(), incomes.EI(), incomes.CPP(), incomes.OAS(), incomes.GIS()]
    self.funds = [funds.TFSA(), funds.RRSP(), funds.NonRegistered()]
    self.involuntary_retirement_random = random.random()
    

  def AnnualSetup(self):
    """This is responsible for beginning of year operations.

    Returns a partially initialized year record.
    """
    year_rec = utils.YearRecord()
    year_rec.age = self.age
    year_rec.year = self.year

    # Reap souls
    if self.gender == MALE:
      p_mortality = world.MALE_MORTALITY[self.age] * world.MORTALITY_MULTIPLIER
    elif self.gender == FEMALE:
      p_mortality = world.FEMALE_MORTALITY[self.age] * world.MORTALITY_MULTIPLIER

    if random.random() < p_mortality:
      year_rec.is_dead = True
      return year_rec
    else:
      year_rec.is_dead = False

    # Retirement
    if not self.retired:
      if ((self.age == self.strategy.planned_retirement_age and self.age >= world.MINIMUM_RETIREMENT_AGE) or
          self.involuntary_retirement_random < (self.age - world.MINIMUM_RETIREMENT_AGE + 1) * world.INVOLUNTARY_RETIREMENT_INCREMENT):
        self.retired = True
        for income in self.incomes:
          income.OnRetirement(self)
    year_rec.is_retired = self.retired

    # Employment
    year_rec.is_employed = not self.is_retired and random.random() > world.UNEMPLOYMENT_PROBABILITY

    # Growth
    year_rec.growth_rate = random.normalvariate(world.MEAN_INVESTMENT_RETURN, world.STD_INVESTMENT_RETURN)


  def CalcIncomeTax(self, year_rec):
    """Calculates the amount of income tax to be paid"""
    return 0

  def MeddleWithCash(self, year_rec):
    """This performs all operations on subject's cash pile"""
    cash = 0

    # Get money from incomes
    for income in self.incomes:
      amount, taxable, year_rec = income.GiveMeMoney(year_rec)
      cash += amount

    # Do withdrawals
    if self.is_retired:
      pass
    else:
      if cash < world.LICO_SINGLE_CITY_WP * self.strategy.lico_target_fraction:
        # Attempt to withdraw difference from savings
        amount_to_withdraw = world.LICO_SINGLE_CITY_WP * self.strategy.lico_target_fraction - cash
        proportions = (self.strategy.working_period_drawdown_tfsa_fraction, self.strategy.working_period_drawdown_nonreg_fraction, 1)
        fund_chain = [f for f in self.funds if f.fund_type == funds.FUND_TYPE_TFSA] + [f for f in self.funds if f.fund_type == funds.FUND_TYPE_NONREG] + [f for f in self.funds if f.fund_type == funds.FUND_TYPE_RRSP]
        withdrawn, gains, year_rec = funds.ChainedWithdraw(amount_to_withdraw, fund_chain, proportions, year_rec)
        cash += withdrawn


    # DO EI/CPP contributions
    earnings = sum(receipt.amount for receipt in year_rec.incomes
                   if receipt.income_type = incomes.INCOME_TYPE_EARNINGS)
		
    if earnings - world.YBE < 0:
      cpp_effective_earnings = 0
    else:
      cpp_effective_earnings = earnings
    year_rec.pensionable_earnings = min(utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE), cpp_effective_earnings)
    cpp_contribution = year_rec.pensionable_earnings * world.CPP_EMPLOYEE_RATE

		year_rec.insurable_earnings = min(utils.Indexed(world.EI_MAX_INSURABLE_EARNINGS, year_rec.year, 1 + world.PARGE), earnings)
    ei_contribution = year_rec.insurable_earnings * world.EI_PREMIUM_RATE
    cash -= cpp_contribution + ei_contribution

    # Save
    earnings_to_save = max(earnings-self.strategy.savings_threshold, 0) * self.strategy.savings_rate
    proportions = (self.strategy.savings_rrsp_fraction, self.strategy.savings_tfsa_fraction, 1)
    fund_chain = [f for f in self.funds if f.fund_type == funds.FUND_TYPE_RRSP] + [f for f in self.funds if f.fund_type == funds.FUND_TYPE_TFSA] + [f for f in self.funds if f.fund_type == funds.FUND_TYPE_NONREG] 
    deposited, year_rec = funds.ChainedDeposit(earnings_to_save, fund_chain, proportions, year_rec)
    cash -= deposited

   
    # Update funds
    for fund in self.funds:
      fund.Update(year_rec)

    # Pay income taxes
    cash -= self.CalcIncomeTax(year_rec)
    
    # Update incomes
    for income in self.incomes:
      income.AnnualUpdate(year_rec)

    # Pay sales tax


  def AnnualReview(self, year_rec):
    """End of year calculations for a live person"""
    self.age += 1
    self.year += 1


  def EndOfLifeCalcs(self):
    """Calculations that happen upon death"""

  def DoYear(self):
    """Execute one year of life"""
    year_rec = self.AnnualSetup()
    if not year_rec.is_dead:
      year_rec = self.MeddleWithCash(year_rec)
      self.AnnualReview(year_rec)
    else:
      self.EndOfLifeCalcs()

  def LiveLife(self):
    """Run through one lifetime"""

