import unittest
import world

class ExtendedDictTest(unittest.TestCase):

  def testMinWithdrawFraction(self):
    self.assertEqual(world.MINIMUM_WITHDRAWAL_FRACTION[45], 0)
    self.assertEqual(world.MINIMUM_WITHDRAWAL_FRACTION[70], 0)
    self.assertEqual(world.MINIMUM_WITHDRAWAL_FRACTION[85], 0.0851)
    self.assertEqual(world.MINIMUM_WITHDRAWAL_FRACTION[95], 0.2000)
    self.assertEqual(world.MINIMUM_WITHDRAWAL_FRACTION[105], 0.2000)

  def testMaleMortality(self):
    self.assertEqual(world.MALE_MORTALITY[0], 0.00577)
    self.assertEqual(world.MALE_MORTALITY[109], 0.63320)
    self.assertEqual(world.MALE_MORTALITY[120], 1.0)

  def testFemaleMortality(self):
    self.assertEqual(world.FEMALE_MORTALITY[0], 0.00467)
    self.assertEqual(world.FEMALE_MORTALITY[109], 0.54200)
    self.assertEqual(world.FEMALE_MORTALITY[120], 1.0)

  def testCEDProportions(self):
    self.assertAlmostEqual(world.CED_PROPORTION[60], 0.05437981)
    self.assertAlmostEqual(world.CED_PROPORTION[110], 1.0)
    self.assertAlmostEqual(world.CED_PROPORTION[120], 1.0)

  def testTaxSchedule(self):
    self.assertEqual(world.FEDERAL_TAX_SCHEDULE[0], 0)
    self.assertEqual(world.FEDERAL_TAX_SCHEDULE[87907], 16263)
    self.assertEqual(world.FEDERAL_TAX_SCHEDULE[-1234], 0)
    self.assertEqual(world.FEDERAL_TAX_SCHEDULE[10200000], 2928837)
    self.assertAlmostEqual(world.FEDERAL_TAX_SCHEDULE[10000], 1500.01137578)

if __name__ == '__main__':
  unittest.main()
