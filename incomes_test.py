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
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 13393.12386743)

  def testCPPRetired65AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*42 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 65
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 14120.69627212)

  def testCPPRetired68AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*45 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 68
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 18214.806497306)

  def testCPPRetired72AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*49 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 72
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 21497.802690981)

  def testCPPRetired63AllPositiveEarnings(self):
    income = incomes.CPP()
    income.ympe_fractions = [0.8]*40 + [0]*5
    fake_person = unittest.mock.MagicMock()
    fake_person.age = 63
    income.OnRetirement(fake_person)
    self.assertAlmostEqual(income.benefit_amount, 11849.148131491)
    


if __name__ == '__main__':
  unittest.main()
