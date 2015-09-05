import utils
import funds
import utils
import world

MALE = "m"
FEMALE = "f"

class Person(object):
  
  def __init__(self, gender=FEMALE):
    self.year = world.BASE_YEAR
    self.age = world.START_AGE
    self.gender = gender
    self.employed_last_year = True
    self.retired = False
    self.incomes = [incomes.Earnings(), incomes.EI(), incomes.CPP(), incomes.OAS(), incomes.GIS()]
    self.funds = [funds.TFSA(), funds.RRSP(), funds.NonRegistered()]
    

  def AnnualSetup(self):
    """This is responsible for beginning of year operations.

    Returns a partially initialized year record.
    """

    year_rec = utils.YearRecord()
    year_rec.age = self.age
    year_rec.year = self.year

    year_rec.is_dead = False  # TODO: Reap souls
    year_rec.is_employed = not self.is_retired # TODO: Calculate possiblity of unemployment
    year_rec.is_retired = self.retired

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
    cpp_contribution = min(utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE), max(0, earnings - world.YBE)) * world.CPP_EMPLOYEE_RATE

		year_rec.insurable_earnings = min(utils.Indexed(world.EI_MAX_INSURABLE_EARNINGS, year_rec.year, 1 + world.PARGE), earnings)
    ei_contribution = year_rec.insurable_earnings * world.EI_PREMIUM_RATE
    cash -= cpp_contribution + ei_contribution

    # Save

    # Pay income taxes
    cash -= self.CalcIncomeTax(year_rec)

    # Pay sales tax


  def AnnualReview(self, year_rec):
    """End of year calculations for a live person"""
    self.age++
    self.year++

  def EndOfLifeCalcs(self):
    """Calculations that happen upon death"""

  def DoYear(self):
    """Execute one year of life"""
    year_rec =self. AnnualSetup()
    if not year_rec.is_dead:
      year_rec = self.MeddleWithCash(year_rec)
      self.AnnualReview(year_rec)
    else:
      self.EndOfLifeCalcs()

  def LiveLife(self):
    """Run through one lifetime"""

