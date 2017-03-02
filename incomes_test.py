import unittest
import unittest.mock
import incomes
import funds
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

  def testGISCalcIncomeBaseUsesLesserIncome(self):
    income = incomes.GIS()
    income.last_year_income_base = 5000
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(8000, incomes.INCOME_TYPE_EARNINGS)]
    year_rec.ei_premium = 0
    year_rec.cpp_contribution = 0
    self.assertEqual(income._CalcIncomeBase(year_rec), 5000)
    self.assertEqual(income.last_year_income_base, 8000)

  def testGISCalcIncomeBaseIncomes(self):
    income = incomes.GIS()
    income.last_year_income_base = 10000
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(1000, incomes.INCOME_TYPE_EARNINGS),
                        incomes.IncomeReceipt(2000, incomes.INCOME_TYPE_CPP),
                        incomes.IncomeReceipt(3000, incomes.INCOME_TYPE_EI)]
    year_rec.ei_premium = 0
    year_rec.cpp_contribution = 0
    self.assertEqual(income._CalcIncomeBase(year_rec), 6000)

  def testGISCalcIncomeBaseRRSPWithdrawals(self):
    income = incomes.GIS()
    income.last_year_income_base = 10000
    year_rec = utils.YearRecord()
    year_rec.withdrawals = [funds.WithdrawReceipt(2000, 0, funds.FUND_TYPE_RRSP),
                            funds.WithdrawReceipt(3000, 0, funds.FUND_TYPE_BRIDGING)] 
    year_rec.ei_premium = 0
    year_rec.cpp_contribution = 0
    self.assertEqual(income._CalcIncomeBase(year_rec), 5000)

  def testGISCalcIncomeBaseCapitalGains(self):
    income = incomes.GIS()
    income.last_year_income_base = 10000
    year_rec = utils.YearRecord()
    year_rec.withdrawals = [funds.WithdrawReceipt(2000, 1000, funds.FUND_TYPE_NONREG)]
    year_rec.tax_receipts = [funds.TaxReceipt(500, funds.FUND_TYPE_NONREG)]
    year_rec.ei_premium = 0
    year_rec.cpp_contribution = 0
    self.assertEqual(income._CalcIncomeBase(year_rec), 750)

  def testGISCalcIncomeBaseIncomesAndPayrollDeductions(self):
    income = incomes.GIS()
    income.last_year_income_base = 10000
    year_rec = utils.YearRecord()
    year_rec.incomes = [incomes.IncomeReceipt(5000, incomes.INCOME_TYPE_EARNINGS)]
    year_rec.ei_premium = 2000
    year_rec.cpp_contribution = 2000
    self.assertEqual(income._CalcIncomeBase(year_rec), 1000)
    

  def setUpYearRecForGIS(self, income_base=0, cpi=1, has_oas=True):
    year_rec = utils.YearRecord()
    year_rec.cpi = cpi
    year_rec.incomes = []
    if has_oas:
      year_rec.incomes.append(incomes.IncomeReceipt(world.OAS_BENEFIT, incomes.INCOME_TYPE_OAS))

    # We want to force some values for the current year's income base
    year_rec.ei_premium = 0
    year_rec.cpp_contribution = 0
    year_rec.incomes.append(incomes.IncomeReceipt(income_base, incomes.INCOME_TYPE_EARNINGS))
    
    return year_rec    

  def testGISBenefitPositiveIncomeNoOAS(self):
    income = incomes.GIS()
    income.last_year_income_base = 1000
    year_rec = self.setUpYearRecForGIS(has_oas=False, income_base=1000)
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, 0)
    self.assertFalse(taxable)
    self.assertIn(incomes.IncomeReceipt(0, incomes.INCOME_TYPE_GIS),
                  year_rec.incomes)

  def testGISBenefitIncomeBelowClawbackExemption(self):
    """Income base is below clawback exemption and supplement exemption"""
    income = incomes.GIS()
    income.last_year_income_base = 10
    year_rec = self.setUpYearRecForGIS(has_oas=True, income_base=10)
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertAlmostEqual(amount, 9925.64)

  def testGISBenefitIncomeBelowSupplementExemption(self):
    """Income base is below supplement exemption but above clawback exemption"""
    income = incomes.GIS()
    income.last_year_income_base = 1000
    year_rec = self.setUpYearRecForGIS(has_oas=True, income_base=1000)
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertAlmostEqual(amount, 9431.64)

  def testGISBenefitPositiveIncome(self):
    """Income base is above both clawback and supplement exemption"""
    income = incomes.GIS()
    income.last_year_income_base = 5000
    year_rec = self.setUpYearRecForGIS(has_oas=True, income_base=5000)
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertAlmostEqual(amount, 7289.46)

  def testGISBenefitPositiveIncomeWithInflation(self):
    """Income base is above both clawback and supplement exemption"""
    income = incomes.GIS()
    income.last_year_income_base = 5000
    year_rec = self.setUpYearRecForGIS(has_oas=True, income_base=5000, cpi=2)
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertAlmostEqual(amount, 17357.28)

  def testGISBenefitPositiveIncomeNoSupplement(self):
    """Getting regular GIS benefit but supplemental GIS benefit should be 0"""
    income = incomes.GIS()
    income.last_year_income_base = 10000
    year_rec = self.setUpYearRecForGIS(has_oas=True, income_base=10000)
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertAlmostEqual(amount, 4021.37)

  def testGISBenefitReallyPositiveIncome(self):
    """Regular and supplemental GIS benefit should both be 0"""
    income = incomes.GIS()
    income.last_year_income_base = 20000
    year_rec = self.setUpYearRecForGIS(has_oas=True, income_base=20000)
    amount, _, _ = income.GiveMeMoney(year_rec)
    self.assertEqual(amount, 0)


if __name__ == '__main__':
  unittest.main()
