import unittest
import unittest.mock
import incomes
import utils

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
									this_year_rec.incomes)

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
		self.assertEqual(amount, 55)
		self.assertEqual(taxable, True)
		self.assertIn(incomes.IncomeReceipt(55, incomes.INCOME_TYPE_EI),
									this_year_rec.incomes)

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
									this_year_rec.incomes)

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
									this_year_rec.incomes)

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
									this_year_rec.incomes)


if __name__ == '__main__':
  unittest.main()
