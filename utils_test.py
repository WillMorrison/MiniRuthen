import unittest
import utils
import world

class UtilsTest(unittest.TestCase):
  
  def testIndexed(self):
    self.assertAlmostEqual(utils.Indexed(100, world.BASE_YEAR + 1, 1.10), 110)
    self.assertAlmostEqual(utils.Indexed(100, world.BASE_YEAR, 123), 100)
    self.assertAlmostEqual(utils.Indexed(100, world.BASE_YEAR + 1), 101)

  def testSummaryStatsAccumulatorUpdateOneValue(self):
    acc = utils.SummaryStatsAccumulator()
    for i in range(2, 52, 2):
      acc.UpdateOneValue(i)

    self.assertEqual(acc.n, 25)
    self.assertAlmostEqual(acc.mean, 26)
    self.assertAlmostEqual(acc.M2, 5200)
    self.assertAlmostEqual(acc.variance, 216.666666667)
    self.assertAlmostEqual(acc.stddev, 14.719601444)

  def testSummaryStatsAccumulatorUpdateOneValueBigNumbers(self):
    acc = utils.SummaryStatsAccumulator()
    for i in range(1000000002, 1000000052, 2):
      acc.UpdateOneValue(i)

    self.assertEqual(acc.n, 25)
    self.assertAlmostEqual(acc.mean, 1000000026)
    self.assertAlmostEqual(acc.M2, 5200)
    self.assertAlmostEqual(acc.variance, 216.666666667)
    self.assertAlmostEqual(acc.stddev, 14.719601444)
  
  def testSummaryStatsAccumulatorUpdateSubsample(self):
    acc1 = utils.SummaryStatsAccumulator()
    acc2 = utils.SummaryStatsAccumulator()
    for i in range(2, 26, 2):
      acc1.UpdateOneValue(i)
    for i in range(26, 52, 2):
      acc2.UpdateOneValue(i)
    acc1.UpdateSubsample(acc2.n, acc2.mean, acc2.M2)

    self.assertEqual(acc1.n, 25)
    self.assertAlmostEqual(acc1.mean, 26)
    self.assertAlmostEqual(acc1.M2, 5200)
    self.assertAlmostEqual(acc1.variance, 216.666666667)
    self.assertAlmostEqual(acc1.stddev, 14.719601444)
  
  def testSummaryStatsAccumulatorUpdateSubsampleBigNumbers(self):
    acc1 = utils.SummaryStatsAccumulator()
    acc2 = utils.SummaryStatsAccumulator()
    for i in range(1000000002, 1000000026, 2):
      acc1.UpdateOneValue(i)
    for i in range(1000000026, 1000000052, 2):
      acc2.UpdateOneValue(i)
    acc1.UpdateSubsample(acc2.n, acc2.mean, acc2.M2)

    self.assertEqual(acc1.n, 25)
    self.assertAlmostEqual(acc1.mean, 1000000026)
    self.assertAlmostEqual(acc1.M2, 5200)
    self.assertAlmostEqual(acc1.variance, 216.666666667)
    self.assertAlmostEqual(acc1.stddev, 14.719601444)

if __name__ == '__main__':
  unittest.main()
