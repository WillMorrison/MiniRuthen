import collections
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
                                   "working_period_drawdown_rrsp_fraction",
                                   "working_period_drawdown_tfsa_fraction",
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
    

  def AnnualSetup(self):
    """This is responsible for beginning of year operations.

    Returns a partially initialized year record.
    """
		# TODO Fate

    year_rec = utils.YearRecord()
    year_rec.age = self.age
    year_rec.year = self.year

    year_rec.is_dead = False  # TODO: Reap souls
    year_rec.is_employed = not self.is_retired  # TODO: Calculate possiblity of unemployment
    year_rec.is_retired = self.retired  # TODO proper retirement calculations

		# TODO Update CPP upon retirement

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
    # TODO Proportions will need to take RRSP bridging funds into account when they are added
    proportions = (self.strategy.savings_rrsp_fraction, self.strategy.savings_tfsa_fraction, 1)
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

