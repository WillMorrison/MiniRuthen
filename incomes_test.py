import unittest
import unittest.mock
import incomes
import utils
import world

class IncomeTest(unittest.TestCase):
  
  def testGiveMeMoney(self):
    income = incomes.Income()
    amount, taxable, year_rec = income.GiveMeMoney(utils.YearRecord())
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_NONE),
                  year_rec.incomes)

  def testEarningsEmployed(self):
    income = incomes.Earnings()
    year_rec = utils.YearRecord()
    year_rec.is_employed = True
    with unittest.mock.patch('random.normalvariate') as my_random:
      my_random.return_value = 10000
      amount, taxable, year_rec = income.GiveMeMoney(year_rec)
      self.assertEqual(amount, 10000)
      self.assertEqual(taxable, True)
      self.assertIn(incomes.IncomeReceipt(10000, incomes.INCOME_TYPE_EARNINGS),
                    year_rec.incomes)

  def testEarningsEmployedNegativeRandom(self):
    income = incomes.Earnings()
    year_rec = utils.YearRecord()
    year_rec.is_employed = True
    with unittest.mock.patch('random.normalvariate') as my_random:
      my_random.return_value = -10000
      amount, taxable, year_rec = income.GiveMeMoney(year_rec)
      self.assertEqual(amount, 0)
      self.assertEqual(taxable, True)
      self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_EARNINGS),
                    year_rec.incomes)

  def testEarningsUnemployed(self):
    income = incomes.Earnings()
    amount, taxable, year_rec = income.GiveMeMoney(utils.YearRecord())
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_EARNINGS),
                  year_rec.incomes)

  def testEIBenefitsEmployedInsuredWorking(self):
    income = incomes.EI()
    last_year_rec = utils.YearRecord()
    last_year_rec.is_employed = True
    last_year_rec.insurable_earnings = 100
    this_year_rec = utils.YearRecord()
    this_year_rec.is_employed = True
    this_year_rec.is_retired = False
    income.AnnualUpdate(last_year_rec)
    amount, taxable, year_rec = income.GiveMeMoney(this_year_rec)
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_EI),
                  year_rec.incomes)

  def testEIBenefitsUnemployedInsuredWorking(self):
    income = incomes.EI()
    last_year_rec = utils.YearRecord()
    last_year_rec.is_employed = True
    last_year_rec.insurable_earnings = 100
    this_year_rec = utils.YearRecord()
    this_year_rec.is_employed = False
    this_year_rec.is_retired = False
    income.AnnualUpdate(last_year_rec)
    amount, taxable, year_rec = income.GiveMeMoney(this_year_rec)
    self.assertAlmostEqual(amount, 55)
    self.assertEqual(taxable, True)
		# done differently due to floating point equality checks
    self.assertEqual(year_rec.incomes[0].income_type, incomes.INCOME_TYPE_EI)
    self.assertAlmostEqual(year_rec.incomes[0].amount, 55)
    self.assertEqual(len(year_rec.incomes), 1)

  def testEIBenefitsUnemployedUninsuredWorking(self):
    income = incomes.EI()
    last_year_rec = utils.YearRecord()
    last_year_rec.is_employed = False
    last_year_rec.insurable_earnings = 0
    this_year_rec = utils.YearRecord()
    this_year_rec.is_employed = False
    this_year_rec.is_retired = False
    income.AnnualUpdate(last_year_rec)
    amount, taxable, year_rec = income.GiveMeMoney(this_year_rec)
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_EI),
                  year_rec.incomes)

  def testEIBenefitsUnemployedInsuredRetired(self):
    income = incomes.EI()
    last_year_rec = utils.YearRecord()
    last_year_rec.is_employed = True
    last_year_rec.insurable_earnings = 100
    this_year_rec = utils.YearRecord()
    this_year_rec.is_employed = False
    this_year_rec.is_retired = True
    income.AnnualUpdate(last_year_rec)
    amount, taxable, year_rec = income.GiveMeMoney(this_year_rec)
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_EI),
                  year_rec.incomes)

  def testEIBenefitsUnemployedUninsuredRetired(self):
    income = incomes.EI()
    last_year_rec = utils.YearRecord()
    last_year_rec.is_employed = False
    last_year_rec.insurable_earnings = 0
    this_year_rec = utils.YearRecord()
    this_year_rec.is_employed = False
    this_year_rec.is_retired = True
    income.AnnualUpdate(last_year_rec)
    amount, taxable, year_rec = income.GiveMeMoney(this_year_rec)
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_EI),
                  year_rec.incomes)

  def testCPPDuringWorkingPeriod(self):
    income = incomes.CPP()
    amount, taxable, year_rec = income.GiveMeMoney(utils.YearRecord())
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_CPP),
                  year_rec.incomes)

  def testCPPAnnualUpdatePositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = []
    year_rec = utils.YearRecord()
    year_rec.is_retired = False
    year_rec.pensionable_earnings = 100
    income.AnnualUpdate(year_rec)
    self.assertEqual(income.ympe_fractions, [100/world.YMPE])

  def testCPPAnnualUpdateZeroEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = []
    year_rec = utils.YearRecord()
    year_rec.is_retired = False
    year_rec.pensionable_earnings = 0
    income.AnnualUpdate(year_rec)
    self.assertEqual(income.ympe_fractions, [0])

  def testCPPRetired65IncludesZeroEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*37 + [0]*10
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 65
    fake_person.year = 2049
    fake_person.cpi_history = [1, 1, 1, 1, 1, 1]
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 13694.3691932)

  def testCPPRetired65AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*42 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 65
    fake_person.year = 2049
    fake_person.cpi_history = [1, 1, 1, 1, 1, 1]
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 14438.3065467)

  def testCPPRetired68AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*45 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 68
    fake_person.year = 2052
    fake_person.cpi_history = [1, 1, 1, 1, 1, 1]
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 18624.5036950)

  def testCPPRetired72AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*49 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 72
    fake_person.year = 2056
    fake_person.cpi_history = [1, 1, 1, 1, 1, 1]
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 21981.3428000)

  def testCPPRetired63AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*40 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 63
    fake_person.year = 2047
    fake_person.cpi_history = [1, 1, 1, 1, 1, 1]
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 12115.6655268)

  def testCPPRetired65AllPositiveEarningsWithInflation(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*42 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 65
    fake_person.year = 2049
    # We use a silly value for the current year's CPI to check we aren't using it.
    fake_person.cpi_history = [1, 1.02, 1.0404, 1.061208, 1.08243216, 100]
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 15033.4266907)

  def testOASBeforeRetirement(self):
    income = incomes.OAS()
    year_rec = utils.YearRecord()
    year_rec.age = 60
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, 0)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_OAS),
                  year_rec.incomes)

  def testOASAtRetirement(self):
    income = incomes.OAS()
    year_rec = utils.YearRecord()
    year_rec.age = 65
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, world.OAS_BENEFIT)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(world.OAS_BENEFIT, incomes.INCOME_TYPE_OAS),
                  year_rec.incomes)

  def testOASAfterRetirement(self):
    income = incomes.OAS()
    year_rec = utils.YearRecord()
    year_rec.age = 70
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, world.OAS_BENEFIT)
    self.assertEqual(taxable, True)
    self.assertIn(incomes.IncomeReceipt(world.OAS_BENEFIT, incomes.INCOME_TYPE_OAS),
                  year_rec.incomes)

  def testOASUsesLastYearsCPI(self):
    income = incomes.OAS()
    year_rec = utils.YearRecord()
    year_rec.age = 65
    year_rec.cpi = 1
    income.AnnualUpdate(year_rec)
    year_rec.age = 66
    year_rec.cpi = 1.02
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, world.OAS_BENEFIT)

  def testGISBenefitPositiveIncomeNoOAS(self):
    income = incomes.GIS()
    income.gis_income = 1000
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(0, incomes.INCOME_TYPE_OAS)]
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, 0)
    self.assertFalse(taxable)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_GIS),
                  year_rec.incomes)

  def testGISBenefitPositiveIncome(self):
    income = incomes.GIS()
    income.gis_income = 1000
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(world.OAS_BENEFIT, incomes.INCOME_TYPE_OAS)]
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, 8521.37)
    self.assertFalse(taxable)
    self.assertIn(incomes.IncomeReceipt(8521.37, incomes.INCOME_TYPE_GIS),
                  year_rec.incomes)

  def testGISBenefitIncomeBelowClawbackExemption(self):
    income = incomes.GIS()
    income.gis_income = 10
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(world.OAS_BENEFIT, incomes.INCOME_TYPE_OAS)]
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, world.GIS_SINGLES_RATE)
    self.assertFalse(taxable)
    self.assertIn(incomes.IncomeReceipt(world.GIS_SINGLES_RATE, incomes.INCOME_TYPE_GIS),
                  year_rec.incomes)

  def testGISBenefitReallyPositiveIncome(self):
    income = incomes.GIS()
    income.gis_income = 20000
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(world.OAS_BENEFIT, incomes.INCOME_TYPE_OAS)]
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, 0)
    self.assertFalse(taxable)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_GIS),
                  year_rec.incomes)

  def testGISAnnualUpdateNoOAS(self):
    income = incomes.GIS()
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(0, incomes.INCOME_TYPE_OAS)]
    year_rec.net_income = 5000
    income.AnnualUpdate(year_rec)
    self.assertEqual(income.gis_income, 5000)
  
  def testGISAnnualUpdateSomeOAS(self):
    income = incomes.GIS()
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(2500, incomes.INCOME_TYPE_OAS)]
    year_rec.net_income = 5000
    income.AnnualUpdate(year_rec)
    self.assertEqual(income.gis_income, 2500)
  
  def testGISAnnualUpdateLotsOfOAS(self):
    income = incomes.GIS()
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(2500, incomes.INCOME_TYPE_OAS)]
    year_rec.net_income = 500
    income.AnnualUpdate(year_rec)
    self.assertEqual(income.gis_income, 0)



if __name__ == '__main__':
  unittest.main()
