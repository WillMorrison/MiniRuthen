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

  def assertHistogramsEqual(self, hist1, hist2, places=7):
    """Compares two lists of (float, int) tuples for equality."""
    fail = False
    if len(hist1) != len(hist2):
      fail = True
    else:
      for a, b in zip(hist1, hist2):
        if round(a[0]-b[0], places) != 0 or a[1] != b[1]:
          fail = True
    if fail:
      self.fail("Histograms differ: a=%r, b=%r" % (hist1, hist2))

  def testQuantileAccumulatorUpdateOneValueNoMerge(self):
    acc = utils.QuantileAccumulator(max_bins=3)
    acc.UpdateOneValue(5)
    acc.UpdateOneValue(22)
    acc.UpdateOneValue(9)

    self.assertHistogramsEqual(acc.bins, [(5, 1), (9, 1), (22, 1)])

  def testQuantileAccumulatorUpdateOneValueMerge(self):
    acc = utils.QuantileAccumulator(max_bins=2)
    acc.UpdateOneValue(5)
    acc.UpdateOneValue(22)
    acc.UpdateOneValue(9)

    self.assertHistogramsEqual(acc.bins, [(7, 2), (22, 1)])

  def testQuantileAccumulatorUpdateOneValueIncrement(self):
    acc = utils.QuantileAccumulator(max_bins=2)
    acc.UpdateOneValue(5)
    acc.UpdateOneValue(5)
    acc.UpdateOneValue(5)

    self.assertHistogramsEqual(acc.bins, [(5, 3)])

  def testQuantileAccumulatorUpdateHistogramNoMerge(self):
    acc1 = utils.QuantileAccumulator(max_bins=4)
    acc1.UpdateOneValue(5)
    acc1.UpdateOneValue(22)
    acc2 = utils.QuantileAccumulator(max_bins=2)
    acc2.UpdateOneValue(9)
    acc2.UpdateOneValue(19)

    acc1.UpdateHistogram(acc2.bins)

    self.assertHistogramsEqual(acc1.bins, [(5, 1), (9, 1), (19, 1), (22, 1)])

  def testQuantileAccumulatorUpdateHistogramMerge(self):
    acc1 = utils.QuantileAccumulator(max_bins=2)
    acc1.UpdateOneValue(5)
    acc1.UpdateOneValue(22)
    acc2 = utils.QuantileAccumulator(max_bins=2)
    acc2.UpdateOneValue(9)
    acc2.UpdateOneValue(19)

    acc1.UpdateHistogram(acc2.bins)

    self.assertHistogramsEqual(acc1.bins, [(7, 2), (20.5, 2)])

  def testQuantileAccumulatorUpdateHistogramPaperExample(self):
    acc = utils.QuantileAccumulator(max_bins=5)
    acc.bins = [(2, 1), (9.5, 2), (17.5, 2), (23, 1), (36,1)]
    acc.UpdateHistogram([(32, 1), (30, 1), (45, 1)])

    self.assertHistogramsEqual(acc.bins, [(2, 1), (9.5, 2), (19.3333333, 3), (32.6666667, 3), (45, 1)])

  def testQuantileAccumulatorQuantileLots(self):
    acc = utils.QuantileAccumulator(max_bins=100)
    for i in range(10001):
      acc.UpdateOneValue(i/10)

    self.assertAlmostEqual(acc.Quantile(0.5), 500, places=0)
    self.assertAlmostEqual(acc.Quantile(0.2), 200, places=0)
    self.assertAlmostEqual(acc.Quantile(0.1), 100, places=0)

  def testQuantileAccumulatorQuantileBeforeAfter(self):
    acc = utils.QuantileAccumulator()
    acc.bins = [(1, 10), (2, 5), (3, 10)]

    self.assertAlmostEqual(acc.Quantile(0), 1)
    self.assertAlmostEqual(acc.Quantile(0.1), 1)
    self.assertAlmostEqual(acc.Quantile(0.9), 3)
    self.assertAlmostEqual(acc.Quantile(1), 3)

  def testQuantileAccumulatorQuantileExact(self):
    acc = utils.QuantileAccumulator()
    acc.bins = [(1, 10), (2, 5), (3, 10)]

    self.assertAlmostEqual(acc.Quantile(0.4), 1.6666667)
    self.assertAlmostEqual(acc.Quantile(0.5), 2)
    self.assertAlmostEqual(acc.Quantile(0.6), 2.3333333)


if __name__ == '__main__':
  unittest.main()
