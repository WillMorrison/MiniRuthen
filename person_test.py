import unittest
import unittest.mock
import person
import incomes
import funds
import world
import utils

class PersonTest(unittest.TestCase):

  def setUp(self):
    self.default_strategy = person.Strategy(
        planned_retirement_age=65,
        savings_threshold=0,
        savings_rate=0.1,
        savings_rrsp_fraction=0.1,
        savings_tfsa_fraction=0.2,
        lico_target_fraction=1.0,
        working_period_drawdown_tfsa_fraction=0.5,
        working_period_drawdown_nonreg_fraction=0.5,
        oas_bridging_fraction=1.0,
        drawdown_ced_fraction=0.8,
        initial_cd_fraction=0.04,
        drawdown_preferred_rrsp_fraction=0.35,
        drawdown_preferred_tfsa_fraction=0.5,
        reinvestment_preference_tfsa_fraction=0.8)

  def testCreatePersonHasIncomes(self):
    j_canuck = person.Person(strategy=self.default_strategy)
    self.assertCountEqual(
        [inc.income_type for inc in j_canuck.incomes],
        [incomes.INCOME_TYPE_EARNINGS,
         incomes.INCOME_TYPE_EI,
         incomes.INCOME_TYPE_CPP,
         incomes.INCOME_TYPE_OAS,
         incomes.INCOME_TYPE_GIS])

  def testCreatePersonHasFunds(self):
    j_canuck = person.Person(strategy=self.default_strategy)

    self.assertEqual(j_canuck.funds["wp_tfsa"].fund_type, funds.FUND_TYPE_TFSA)
    self.assertEqual(j_canuck.funds["wp_tfsa"].amount, 0)
    self.assertEqual(j_canuck.funds["wp_rrsp"].fund_type, funds.FUND_TYPE_RRSP)
    self.assertEqual(j_canuck.funds["wp_rrsp"].amount, 0)
    self.assertEqual(j_canuck.funds["wp_nonreg"].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(j_canuck.funds["wp_nonreg"].amount, 0)

  def testCreatePersonFundRoom(self):
    j_canuck = person.Person(strategy=self.default_strategy)
    self.assertEqual(j_canuck.tfsa_room, world.TFSA_INITIAL_CONTRIBUTION_LIMIT)
    self.assertEqual(j_canuck.rrsp_room, world.RRSP_INITIAL_LIMIT)

  def testCreatePersonParameters(self):
    j_canuck = person.Person(strategy=self.default_strategy)
    self.assertEqual(j_canuck.strategy, self.default_strategy)
    self.assertEqual(j_canuck.gender, person.FEMALE)

    j_canuck = person.Person(strategy=self.default_strategy, gender=person.MALE)
    self.assertEqual(j_canuck.gender, person.MALE)

  @unittest.mock.patch('random.random')
  def testAnnualSetupReaper(self, mock_random):
    # Female, random variate < mortality probability at age 30
    j_canuck = person.Person(strategy=self.default_strategy, gender=person.FEMALE)
    j_canuck.age = 30
    mock_random.return_value = 0.0003
    year_rec = j_canuck.AnnualSetup()
    self.assertTrue(year_rec.is_dead)

    # Female, random variate > mortality probability at age 30
    j_canuck = person.Person(strategy=self.default_strategy, gender=person.FEMALE)
    j_canuck.age = 30
    mock_random.return_value = 0.0004
    year_rec = j_canuck.AnnualSetup()
    self.assertFalse(year_rec.is_dead)

    # Male, random variate < mortality probability at age 30
    j_canuck = person.Person(strategy=self.default_strategy, gender=person.MALE)
    j_canuck.age = 30
    mock_random.return_value = 0.0008
    year_rec = j_canuck.AnnualSetup()
    self.assertTrue(year_rec.is_dead)

    # Male, random variate > mortality probability at age 30
    j_canuck = person.Person(strategy=self.default_strategy, gender=person.MALE)
    j_canuck.age = 30
    mock_random.return_value = 0.0009
    year_rec = j_canuck.AnnualSetup()
    self.assertFalse(year_rec.is_dead)

  # Make sure all incomes have GiveMeMoney called in a year (even if they don't return anything)
  @unittest.mock.patch('random.random')
  def testAllIncomesGetUsed(self, mock_random):
    mock_random.return_value = 0.5  # ensure the person doesn't die the first year
    j_canuck = person.Person(strategy=self.default_strategy)
    year_rec = j_canuck.AnnualSetup()
    year_rec = j_canuck.MeddleWithCash(year_rec)
    self.assertCountEqual(
        [receipt.income_type for receipt in year_rec.incomes],
        [incomes.INCOME_TYPE_EARNINGS,
         incomes.INCOME_TYPE_EI,
         incomes.INCOME_TYPE_CPP,
         incomes.INCOME_TYPE_OAS,
         incomes.INCOME_TYPE_GIS])

  @unittest.mock.patch.object(incomes.CPP, 'OnRetirement')
  def testAnnualSetupInvoluntaryRetirement(self, _):
    strategy = self.default_strategy._replace(planned_retirement_age=65)

    # Forced retirement at age 60
    j_canuck = person.Person(strategy=strategy)
    j_canuck.involuntary_retirement_random = 0.05
    j_canuck.age = 60
    year_rec = j_canuck.AnnualSetup()
    self.assertTrue(year_rec.is_retired)
    self.assertTrue(j_canuck.retired)

    # Forced retirement at 61 shouldn't kick in at 60
    j_canuck = person.Person(strategy=strategy)
    j_canuck.involuntary_retirement_random = 0.1
    j_canuck.age = 60
    year_rec = j_canuck.AnnualSetup()
    self.assertFalse(year_rec.is_retired)
    self.assertFalse(j_canuck.retired)

    # Forced retirement at age 61
    j_canuck = person.Person(strategy=strategy)
    j_canuck.involuntary_retirement_random = 0.1
    j_canuck.age = 61
    year_rec = j_canuck.AnnualSetup()
    self.assertTrue(year_rec.is_retired)
    self.assertTrue(j_canuck.retired)

  @unittest.mock.patch.object(incomes.CPP, 'OnRetirement')
  def testAnnualSetupVoluntaryRetirement(self, _):
    strategy = self.default_strategy._replace(planned_retirement_age=65)

    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 64
    j_canuck.involuntary_retirement_random = 1.0
    year_rec = j_canuck.AnnualSetup()
    self.assertFalse(year_rec.is_retired)
    self.assertFalse(j_canuck.retired)
    
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 65
    j_canuck.involuntary_retirement_random = 1.0
    year_rec = j_canuck.AnnualSetup()
    self.assertTrue(year_rec.is_retired)
    self.assertTrue(j_canuck.retired)

  def testAnnualSetupEmployment(self): 
    # Not retired, good random number
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.retired = False
    with unittest.mock.patch('random.random', return_value=0.2):
      year_rec = j_canuck.AnnualSetup()
      self.assertTrue(year_rec.is_employed)

    # Not retired, bad random number
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.retired = False
    with unittest.mock.patch('random.random', return_value=0.1):
      year_rec = j_canuck.AnnualSetup()
      self.assertFalse(year_rec.is_employed)

    # Retired, good random number
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.retired = True
    with unittest.mock.patch('random.random', return_value=0.2):
      year_rec = j_canuck.AnnualSetup()
      self.assertFalse(year_rec.is_employed)

  @unittest.mock.patch('random.normalvariate', return_value=0.05)
  def testAnnualSetupGrowth(self, mock_random):
    j_canuck = person.Person(strategy=self.default_strategy)
    year_rec = j_canuck.AnnualSetup()
    self.assertEqual(year_rec.growth_rate, 0.05)

  @unittest.mock.patch('random.normalvariate', return_value=0.02)
  def testAnnualSetupInflationFirstYear(self, mock_random):
    j_canuck = person.Person(strategy=self.default_strategy)
    year_rec = j_canuck.AnnualSetup()
    self.assertEqual(year_rec.cpi, 1)

  @unittest.mock.patch('random.normalvariate', return_value=0.02)
  def testAnnualSetupInflation(self, mock_random):
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.year = world.BASE_YEAR + 1
    year_rec = j_canuck.AnnualSetup()
    self.assertEqual(year_rec.cpi, 1.02)

  @unittest.mock.patch('random.normalvariate', return_value=0.02)
  def testAnnualSetupCPIHistory(self, mock_random):
    j_canuck = person.Person(strategy=self.default_strategy)
    _ = j_canuck.AnnualSetup()
    j_canuck.year = world.BASE_YEAR + 1
    _ = j_canuck.AnnualSetup()
    self.assertEqual(j_canuck.cpi_history, [1, 1.02])

  def testAnnualSetupRoomTransfer(self):
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.tfsa_room = 30
    j_canuck.rrsp_room = 40

    year_rec = j_canuck.AnnualSetup()

    self.assertEqual(year_rec.tfsa_room, 30 + world.TFSA_ANNUAL_CONTRIBUTION_LIMIT)
    self.assertEqual(year_rec.rrsp_room, 40)  # RRSP room is updated after we have earnings info

  @unittest.mock.patch.object(incomes.CPP, 'OnRetirement')
  def testOnRetirementBridgingFund(self, _):
    strategy = self.default_strategy._replace(planned_retirement_age=63)
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 63
    j_canuck.funds["wp_rrsp"].amount = 5 * world.OAS_BENEFIT
    year_rec = utils.YearRecord()

    j_canuck.OnRetirement(year_rec)

    self.assertIn("bridging", j_canuck.funds)
    self.assertEqual(j_canuck.funds["bridging"].amount, 2 * world.OAS_BENEFIT)

  @unittest.mock.patch.object(incomes.CPP, 'OnRetirement')
  def testOnRetirementBridgingFundNoRRSP(self, _):
    strategy = self.default_strategy._replace(planned_retirement_age=60)
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 60
    j_canuck.funds["wp_rrsp"].amount = 0
    j_canuck.funds["wp_nonreg"].amount = 2 * world.OAS_BENEFIT
    j_canuck.funds["wp_tfsa"].amount = 4 * world.OAS_BENEFIT
    j_canuck.rrsp_room = 6 * world.OAS_BENEFIT
    year_rec = utils.YearRecord()

    j_canuck.OnRetirement(year_rec)

    self.assertIn("bridging", j_canuck.funds)
    self.assertEqual(j_canuck.funds["bridging"].amount, 5 * world.OAS_BENEFIT)
    self.assertIn(funds.WithdrawReceipt(2 * world.OAS_BENEFIT, 0, funds.FUND_TYPE_NONREG), year_rec.withdrawals)
    self.assertIn(funds.WithdrawReceipt(3 * world.OAS_BENEFIT, 0, funds.FUND_TYPE_TFSA), year_rec.withdrawals)
    self.assertAlmostEqual(j_canuck.rrsp_room, world.OAS_BENEFIT)

  @unittest.mock.patch.object(incomes.CPP, 'OnRetirement')
  def testOnRetirementBridgingFundRRSPRoomLimit(self, _):
    strategy = self.default_strategy._replace(planned_retirement_age=60)
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 60
    j_canuck.funds["wp_rrsp"].amount = world.OAS_BENEFIT
    j_canuck.funds["wp_nonreg"].amount = 2 * world.OAS_BENEFIT
    j_canuck.rrsp_room = 0.5 * world.OAS_BENEFIT
    year_rec = utils.YearRecord()

    j_canuck.OnRetirement(year_rec)

    self.assertIn("bridging", j_canuck.funds)
    self.assertEqual(j_canuck.funds["bridging"].amount, 1.5 * world.OAS_BENEFIT)
    self.assertIn(funds.WithdrawReceipt(0.5 * world.OAS_BENEFIT, 0, funds.FUND_TYPE_NONREG), year_rec.withdrawals)
    self.assertEqual(j_canuck.rrsp_room, 0)

  @unittest.mock.patch.object(incomes.CPP, 'OnRetirement')
  def testOnRetirementFundSplitting(self, _):
    strategy = self.default_strategy._replace(drawdown_ced_fraction=0.8,
                                              initial_cd_fraction=0.05)
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 65
    j_canuck.funds["wp_rrsp"].amount = 1500
    j_canuck.funds["wp_tfsa"].amount = 1000
    j_canuck.funds["wp_nonreg"].amount = 500

    j_canuck.OnRetirement(utils.YearRecord())

    self.assertCountEqual(
        j_canuck.funds.keys(),
        ("cd_rrsp", "ced_rrsp", "cd_tfsa", "ced_tfsa", "cd_nonreg", "ced_nonreg"))
    self.assertEqual(j_canuck.funds["cd_rrsp"].amount, 300)
    self.assertEqual(j_canuck.funds["ced_rrsp"].amount, 1200)
    self.assertEqual(j_canuck.funds["cd_tfsa"].amount, 200)
    self.assertEqual(j_canuck.funds["ced_tfsa"].amount, 800)
    self.assertEqual(j_canuck.funds["cd_nonreg"].amount, 100)
    self.assertEqual(j_canuck.funds["ced_nonreg"].amount, 400)
    self.assertEqual(j_canuck.cd_drawdown_amount, 30)

  def SetupYearRecForIncomeTax(
      self, earnings=0, oas=0, gis=0, cpp=0, ei=0,
      rrsp=0, bridging=0,nonreg=0, gains=0, eoy_gains=0,
      unapplied_losses=0, rrsp_contributions=0,
      age=30, retired=False, cpi=1):
    """Set up a person and a year record in one go for testing income tax."""
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.capital_loss_carry_forward = unapplied_losses
    j_canuck.age += age - world.START_AGE
    j_canuck.year += age - world.START_AGE
    j_canuck.retired = retired

    year_rec = utils.YearRecord()
    year_rec.is_retired = j_canuck.retired
    year_rec.year = j_canuck.year
    year_rec.incomes.append(incomes.IncomeReceipt(earnings, incomes.INCOME_TYPE_EARNINGS))
    year_rec.incomes.append(incomes.IncomeReceipt(oas, incomes.INCOME_TYPE_OAS))
    year_rec.incomes.append(incomes.IncomeReceipt(gis, incomes.INCOME_TYPE_GIS))
    year_rec.incomes.append(incomes.IncomeReceipt(cpp, incomes.INCOME_TYPE_CPP))
    year_rec.incomes.append(incomes.IncomeReceipt(ei, incomes.INCOME_TYPE_EI))
    year_rec.withdrawals.append(funds.WithdrawReceipt(nonreg, gains, funds.FUND_TYPE_NONREG))
    year_rec.withdrawals.append(funds.WithdrawReceipt(rrsp, 0, funds.FUND_TYPE_RRSP))
    year_rec.withdrawals.append(funds.WithdrawReceipt(bridging, 0, funds.FUND_TYPE_BRIDGING))
    year_rec.tax_receipts.append(funds.TaxReceipt(eoy_gains, funds.FUND_TYPE_NONREG))
    year_rec.deposits.append(funds.DepositReceipt(rrsp_contributions, funds.FUND_TYPE_RRSP))
    year_rec.cpi = cpi

    year_rec = j_canuck.CalcPayrollDeductions(year_rec)

    return (j_canuck, year_rec)

  def testIncomeTaxEarningsOnly(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(earnings=62000)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 11942.71, delta=0.1)

  def testIncomeTaxEarningsOnlyWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(earnings=62000, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 10877.83, delta=0.1)

  def testIncomeTaxEIOnly(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(ei=7000)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 0, delta=0.1)

  def testIncomeTaxEIOnlyWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(ei=7000, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 0, delta=0.1)

  def testIncomeTaxCPPOnly(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(cpp=10000)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 0, delta=0.1)

  def testIncomeTaxCPPOnlyWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(cpp=10000, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 0, delta=0.1)

  def testIncomeTaxEarningsAndContributions(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(earnings=62000, rrsp_contributions=10000)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 8305.21, delta=0.1)

  def testIncomeTaxEarningsAndContributionsWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(earnings=62000, rrsp_contributions=10000, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 7240.33, delta=0.1)

  def testIncomeTaxGainsOnly(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(nonreg=40000, gains=25000, eoy_gains=15000)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 437.85, delta=0.1)

  def testIncomeTaxGainsOnlyWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(nonreg=40000, gains=25000, eoy_gains=15000, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 31.63, delta=0.1)

  def testIncomeTaxGainsWithCarryForwardLosses(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(nonreg=40000, gains=40000, unapplied_losses=2000)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 212.85, delta=0.1)

  def testIncomeTaxGainsWithCarryForwardLossesWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(nonreg=50000, gains=50000, unapplied_losses=2000, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 931.64, delta=0.1)

  def testIncomeTaxRRSPOnly(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(rrsp=20000, retired=True, age=65)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 437.85, delta=0.1)

  def testIncomeTaxRRSPOnlyWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(rrsp=20000, retired=True, age=65, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 31.63, delta=0.1)

  def testIncomeTaxRRSPAndOASAndGIS(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(rrsp=15000, oas=5000, gis=4000, retired=True, age=65)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 437.85, delta=0.1)

  def testIncomeTaxRRSPAndOASAndGISWithInflation(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(rrsp=15000, oas=5000, gis=4000, retired=True, age=65, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 31.63, delta=0.1)

  def testIncomeTaxRRSPAndBridging(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(rrsp=10000, bridging=10000, retired=True, age=62)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 437.85, delta=0.1)

  def testIncomeTaxRRSPAndBridging(self):
    j_canuck, year_rec = self.SetupYearRecForIncomeTax(rrsp=10000, bridging=10000, retired=True, age=62, cpi=1.1)
    tax_payable = j_canuck.CalcIncomeTax(year_rec)
    self.assertAlmostEqual(tax_payable, 31.63, delta=0.1)

  def SetupForMeddleWithCash(self, age=30, cpi=1, retired=False, employed=True,
                             rrsp=0, rrsp_room=0, tfsa=0, tfsa_room=0, nonreg=0):
    j_canuck = person.Person()
    year_rec = utils.YearRecord()

    # Set working period fund amounts (these may be split later on)
    j_canuck.funds["wp_rrsp"].amount = rrsp
    j_canuck.funds["wp_tfsa"].amount = tfsa
    j_canuck.funds["wp_nonreg"].amount = nonreg

    # The following section roughly approximates Person.AnnualSetup()
    j_canuck.age = age
    year_rec.age = age
    j_canuck.year = age - world.START_AGE + world.BASE_YEAR
    year_rec.year = age - world.START_AGE + world.BASE_YEAR
    j_canuck.cpi = cpi
    year_rec.cpi = cpi

    j_canuck.retired = retired
    if retired:
      j_canuck.OnRetirement()
    year_rec.is_retired = retired
    year_rec.is_employed = employed and not retired

    year_rec.growth_rate = world.MEAN_INVESTMENT_RETURN

    j_canuck.tfsa_room = tfsa_room
    year_rec.tfsa_room = tfsa_room
    j_canuck.rrsp_room = rrsp_room
    year_rec.rrsp_room = rrsp_room

    return j_canuck, year_rec


if __name__ == '__main__':
  unittest.main()
