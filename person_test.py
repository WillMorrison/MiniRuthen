import unittest
import unittest.mock
import person
import incomes
import funds
import world

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

    # Female, random variate > mortality probability at age 30
    j_canuck = person.Person(strategy=self.default_strategy, gender=person.MALE)
    j_canuck.age = 30
    mock_random.return_value = 0.0009
    year_rec = j_canuck.AnnualSetup()
    self.assertFalse(year_rec.is_dead)

  def testAnnualSetupInvoluntaryRetirement(self):
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

  def testAnnualSetupVoluntaryRetirement(self):
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

  def testAnnualSetupRoomTransfer(self):
    j_canuck = person.Person(strategy=self.default_strategy)
    j_canuck.tfsa_room = 30
    j_canuck.rrsp_room = 40

    year_rec = j_canuck.AnnualSetup()

    self.assertEqual(year_rec.tfsa_room, 30)
    self.assertEqual(year_rec.rrsp_room, 40)

  def testOnRetirementBridgingFund(self):
    strategy = self.default_strategy._replace(planned_retirement_age=63)
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 63
    j_canuck.funds["wp_rrsp"].amount = 5 * world.OAS_BENEFIT

    j_canuck.OnRetirement()

    self.assertIn("bridging", j_canuck.funds)
    self.assertEqual(j_canuck.funds["bridging"].amount, 2 * world.OAS_BENEFIT)

  def testOnRetirementFundSplitting(self):
    strategy = self.default_strategy._replace(drawdown_ced_fraction=0.8,
                                              initial_cd_fraction=0.05)
    j_canuck = person.Person(strategy=strategy)
    j_canuck.age = 65
    j_canuck.funds["wp_rrsp"].amount = 1500
    j_canuck.funds["wp_tfsa"].amount = 1000
    j_canuck.funds["wp_nonreg"].amount = 500

    j_canuck.OnRetirement()

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


if __name__ == '__main__':
  unittest.main()
