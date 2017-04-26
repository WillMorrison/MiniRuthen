import math
import unittest
import utils
import person
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
    self.assertEqual(acc.total, 650)
    self.assertAlmostEqual(acc.mean, 26)
    self.assertAlmostEqual(acc.M2, 5200)
    self.assertAlmostEqual(acc.variance, 216.666666667)
    self.assertAlmostEqual(acc.stddev, 14.719601444)
    self.assertAlmostEqual(acc.stderr, 2.9439203)
    self.assertAlmostEqual(acc.cv, 0.5661385)

  def testSummaryStatsAccumulatorUpdateOneValueBigNumbers(self):
    acc = utils.SummaryStatsAccumulator()
    for i in range(1000000002, 1000000052, 2):
      acc.UpdateOneValue(i)

    self.assertEqual(acc.n, 25)
    self.assertEqual(acc.total, 25000000650)
    self.assertAlmostEqual(acc.mean, 1000000026)
    self.assertAlmostEqual(acc.M2, 5200)
    self.assertAlmostEqual(acc.variance, 216.666666667)
    self.assertAlmostEqual(acc.stddev, 14.719601444)
    self.assertAlmostEqual(acc.stderr, 2.9439203)
    self.assertAlmostEqual(acc.cv, 0.0000000)
  
  def testSummaryStatsAccumulatorUpdateSubsample(self):
    acc1 = utils.SummaryStatsAccumulator()
    acc2 = utils.SummaryStatsAccumulator()
    for i in range(2, 26, 2):
      acc1.UpdateOneValue(i)
    for i in range(26, 52, 2):
      acc2.UpdateOneValue(i)
    acc1.UpdateSubsample(acc2.n, acc2.mean, acc2.M2)

    self.assertEqual(acc1.n, 25)
    self.assertEqual(acc1.total, 650)
    self.assertAlmostEqual(acc1.mean, 26)
    self.assertAlmostEqual(acc1.M2, 5200)
    self.assertAlmostEqual(acc1.variance, 216.666666667)
    self.assertAlmostEqual(acc1.stddev, 14.719601444)
    self.assertAlmostEqual(acc1.stderr, 2.9439203)
  
  def testSummaryStatsAccumulatorUpdateSubsampleBigNumbers(self):
    acc1 = utils.SummaryStatsAccumulator()
    acc2 = utils.SummaryStatsAccumulator()
    for i in range(1000000002, 1000000026, 2):
      acc1.UpdateOneValue(i)
    for i in range(1000000026, 1000000052, 2):
      acc2.UpdateOneValue(i)
    acc1.UpdateSubsample(acc2.n, acc2.mean, acc2.M2)

    self.assertEqual(acc1.n, 25)
    self.assertEqual(acc1.total, 25000000650)
    self.assertAlmostEqual(acc1.mean, 1000000026)
    self.assertAlmostEqual(acc1.M2, 5200)
    self.assertAlmostEqual(acc1.variance, 216.666666667)
    self.assertAlmostEqual(acc1.stddev, 14.719601444)
    self.assertAlmostEqual(acc1.stderr, 2.9439203)
  
  def testSummaryStatsAccumulatorUpdateSubsampleEmpty(self):
    acc = utils.SummaryStatsAccumulator()
    acc.UpdateSubsample(0, 0, 0)

    self.assertEqual(acc.n, 0)
    self.assertEqual(acc.total, 0)
    self.assertEqual(acc.mean, 0)
    self.assertEqual(acc.M2, 0)

  def testSummaryStatsAccumulatorNeverUpdated(self):
    acc = utils.SummaryStatsAccumulator()

    self.assertEqual(acc.n, 0)
    self.assertEqual(acc.total, 0)
    self.assertEqual(acc.mean, 0)
    self.assertEqual(acc.M2, 0)
    self.assertTrue(math.isnan(acc.variance), msg="expected NaN")
    self.assertTrue(math.isnan(acc.stddev), msg="expected NaN")
    self.assertTrue(math.isnan(acc.stderr), msg="expected NaN")

  def testSummaryStatsAccumulatorUpdateAccumulator(self):
    acc1 = utils.SummaryStatsAccumulator()
    acc2 = utils.SummaryStatsAccumulator()
    for i in range(2, 26, 2):
      acc1.UpdateOneValue(i)
    for i in range(26, 52, 2):
      acc2.UpdateOneValue(i)
    acc1.UpdateAccumulator(acc2)

    self.assertEqual(acc1.n, 25)
    self.assertEqual(acc1.total, 650)
    self.assertAlmostEqual(acc1.mean, 26)
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

  def testQuantileAccumulatorUpdateAccumulatorNoMerge(self):
    acc1 = utils.QuantileAccumulator(max_bins=4)
    acc1.UpdateOneValue(5)
    acc1.UpdateOneValue(22)
    acc2 = utils.QuantileAccumulator(max_bins=2)
    acc2.UpdateOneValue(9)
    acc2.UpdateOneValue(19)

    acc1.UpdateAccumulator(acc2)

    self.assertHistogramsEqual(acc1.bins, [(5, 1), (9, 1), (19, 1), (22, 1)])

  def testQuantileAccumulatorUpdateAccumulatorMerge(self):
    acc1 = utils.QuantileAccumulator(max_bins=2)
    acc1.UpdateOneValue(5)
    acc1.UpdateOneValue(22)
    acc2 = utils.QuantileAccumulator(max_bins=2)
    acc2.UpdateOneValue(9)
    acc2.UpdateOneValue(19)

    acc1.UpdateAccumulator(acc2)

    self.assertHistogramsEqual(acc1.bins, [(7, 2), (20.5, 2)])
  
  def testQuantileAccumulatorUpdateAccumulatorMergeDuplicateCentroids(self):
    acc1 = utils.QuantileAccumulator(max_bins=5)
    acc1.UpdateOneValue(9)
    acc1.UpdateOneValue(22)
    acc2 = utils.QuantileAccumulator(max_bins=5)
    acc2.UpdateOneValue(9)
    acc2.UpdateOneValue(19)

    acc1.UpdateAccumulator(acc2)

    self.assertHistogramsEqual(acc1.bins, [(9, 2), (19, 1), (22, 1)])

  def testQuantileAccumulatorUpdateHistogramManyDuplicateCentroids(self):
    acc = utils.QuantileAccumulator(max_bins=5)
    acc.bins = [(2, 1), (2, 1), (2, 1), (2, 1), (2, 1)]
    acc.UpdateHistogram([(1, 1), (1, 1), (1, 1)])

    self.assertHistogramsEqual(acc.bins, [(1, 3), (2, 5)])

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

  def testQuantileAccumulatorNeverUpdated(self):
    acc = utils.QuantileAccumulator()
    self.assertTrue(math.isnan(acc.Quantile(0.1)), msg="expected NaN")

  def testKeyedAccumulatorSummaryStatsUpdateOneValue(self):
    acc = utils.KeyedAccumulator(utils.SummaryStatsAccumulator)
    for i in range(2, 52, 2):
      acc.UpdateOneValue(i, 'key')

    subacc = acc.Query(['key'])

    self.assertEqual(subacc.n, 25)
    self.assertAlmostEqual(subacc.mean, 26)
    self.assertAlmostEqual(subacc.M2, 5200)
    self.assertAlmostEqual(subacc.variance, 216.666666667)
    self.assertAlmostEqual(subacc.stddev, 14.719601444)

  def testKeyedAccumulatorQuantileUpdateOneValue(self):
    acc = utils.KeyedAccumulator(utils.QuantileAccumulator, {'max_bins':3})
    acc.UpdateOneValue(5, 'key')
    acc.UpdateOneValue(22, 'key')
    acc.UpdateOneValue(9, 'key')
    subacc = acc.Query(['key'])

    self.assertHistogramsEqual(subacc.bins, [(5, 1), (9, 1), (22, 1)])

  def testKeyedAccumulatorMultipleKeysUpdateOneValue(self):
    acc = utils.KeyedAccumulator(utils.QuantileAccumulator)
    acc.UpdateOneValue(5, 'key1')
    acc.UpdateOneValue(22, 'key1')
    acc.UpdateOneValue(9, 'key2')
    subacc = acc.Query(['key1'])

    self.assertHistogramsEqual(subacc.bins, [(5, 1), (22, 1)])
  
  def testKeyedAccumulatorMultipleKeysQuery(self):
    acc = utils.KeyedAccumulator(utils.QuantileAccumulator)
    acc.UpdateOneValue(5, 'key1')
    acc.UpdateOneValue(22, 'key2')
    acc.UpdateOneValue(9, 'key1')
    subacc = acc.Query(['key1', 'key2'])

    self.assertHistogramsEqual(subacc.bins, [(5, 1), (9, 1), (22, 1)])
  
  def testKeyedAccumulatorSomeMissingKeysQuery(self):
    acc = utils.KeyedAccumulator(utils.QuantileAccumulator)
    acc.UpdateOneValue(5, 'key1')
    acc.UpdateOneValue(22, 'key2')
    acc.UpdateOneValue(9, 'key1')
    subacc = acc.Query(['key1', 'key2', 'key3'])

    self.assertHistogramsEqual(subacc.bins, [(5, 1), (9, 1), (22, 1)])
  
  def testKeyedAccumulatorMissingKeysQueryIsIdempotent(self):
    acc = utils.KeyedAccumulator(utils.QuantileAccumulator)
    subacc = acc.Query(['key'])
    self.assertHistogramsEqual(subacc.bins, [])
    self.assertEqual(len(acc._accumulators), 0)
  
  def testKeyedAccumulatorUpdateAccumulator(self):
    acc1 = utils.KeyedAccumulator(utils.QuantileAccumulator)
    acc2 = utils.KeyedAccumulator(utils.QuantileAccumulator)
    acc1.UpdateOneValue(5, 'key1')
    acc1.UpdateOneValue(22, 'key2')
    acc2.UpdateOneValue(9, 'key1')
    acc2.UpdateOneValue(9, 'key3')

    acc1.UpdateAccumulator(acc2)

    subacc = acc1.Query(['key1', 'key2', 'key3'])
    self.assertHistogramsEqual(subacc.bins, [(5, 1), (9, 2), (22, 1)])
    
    subacc = acc1.Query(['key1'])
    self.assertHistogramsEqual(subacc.bins, [(5, 1), (9, 1)])

  def testAccumulatorBundleUpdateConsumptionWorking(self):
    bundle = utils.AccumulatorBundle()
    bundle.UpdateConsumption(100, year=world.BASE_YEAR+1, is_retired=False, period=person.EMPLOYED)

    self.assertEqual(bundle.lifetime_consumption_summary.mean, 100)
    self.assertHistogramsEqual(bundle.lifetime_consumption_hist.bins, [(100, 1)])
    self.assertAlmostEqual(bundle.discounted_lifetime_consumption_summary.mean, 97)

    self.assertEqual(bundle.working_consumption_summary.mean, 100)
    self.assertHistogramsEqual(bundle.working_consumption_hist.bins, [(100, 1)])

    self.assertEqual(bundle.retired_consumption_summary.n, 0)
    self.assertEqual(bundle.retired_consumption_hist.bins, [])
    self.assertEqual(bundle.pre_disability_retired_consumption_summary.n, 0)

  def testAccumulatorBundleUpdateConsumptionRetiredPreDisability(self):
    sim_years = world.AVG_DISABILITY_AGE - world.START_AGE
    bundle = utils.AccumulatorBundle()
    bundle.UpdateConsumption(100, year=sim_years + world.BASE_YEAR, is_retired=True, period=person.RETIRED)

    self.assertEqual(bundle.lifetime_consumption_summary.mean, 100)
    self.assertHistogramsEqual(bundle.lifetime_consumption_hist.bins, [(100, 1)])
    self.assertAlmostEqual(bundle.discounted_lifetime_consumption_summary.mean, 100 * 0.97 ** sim_years)

    self.assertEqual(bundle.working_consumption_summary.n, 0)
    self.assertEqual(bundle.working_consumption_hist.bins, [])

    self.assertEqual(bundle.retired_consumption_summary.mean, 100)
    self.assertHistogramsEqual(bundle.retired_consumption_hist.bins, [(100, 1)])
    self.assertEqual(bundle.pre_disability_retired_consumption_summary.mean, 100)

  def testAccumulatorBundleUpdateConsumptionRetiredPostDisability(self):
    sim_years = world.AVG_DISABILITY_AGE - world.START_AGE + 1
    bundle = utils.AccumulatorBundle()
    bundle.UpdateConsumption(100, year=sim_years + world.BASE_YEAR, is_retired=True, period=person.RETIRED)

    self.assertEqual(bundle.lifetime_consumption_summary.mean, 100)
    self.assertHistogramsEqual(bundle.lifetime_consumption_hist.bins, [(100, 1)])
    self.assertAlmostEqual(bundle.discounted_lifetime_consumption_summary.mean, 100 * 0.97 ** sim_years)

    self.assertEqual(bundle.working_consumption_summary.n, 0)
    self.assertEqual(bundle.working_consumption_hist.bins, [])

    self.assertEqual(bundle.retired_consumption_summary.mean, 100)
    self.assertHistogramsEqual(bundle.retired_consumption_hist.bins, [(100, 1)])
    self.assertEqual(bundle.pre_disability_retired_consumption_summary.n, 0)

  def testAccumulatorBundleMerge(self):
    sim_years = world.AVG_DISABILITY_AGE - world.START_AGE
    bundle1 = utils.AccumulatorBundle()
    bundle1.UpdateConsumption(200, year=sim_years + world.BASE_YEAR, is_retired=True, period=person.RETIRED)
    bundle2 = utils.AccumulatorBundle()
    bundle2.UpdateConsumption(100, year=world.BASE_YEAR + 1, is_retired=False, period=person.EMPLOYED)
    bundle1.Merge(bundle2)

    self.assertEqual(bundle1.lifetime_consumption_summary.mean, 150)
    self.assertHistogramsEqual(bundle1.lifetime_consumption_hist.bins, [(100, 1), (200, 1)])
    self.assertAlmostEqual(bundle1.discounted_lifetime_consumption_summary.n, 2)

    self.assertEqual(bundle1.working_consumption_summary.n, 1)
    self.assertEqual(bundle1.working_consumption_hist.bins, [(100, 1)])

    self.assertEqual(bundle1.retired_consumption_summary.n, 1)
    self.assertHistogramsEqual(bundle1.retired_consumption_hist.bins, [(200, 1)])
    self.assertEqual(bundle1.pre_disability_retired_consumption_summary.n, 1)


if __name__ == '__main__':
  unittest.main()
