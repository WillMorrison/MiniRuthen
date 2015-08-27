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


if __name__ == '__main__':
  unittest.main()
