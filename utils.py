"""Utils holds miscellaneous classes and functions that don't fit elsewhere."""

import bisect
import collections
import math
import world

class YearRecord(object):
  def __init__(self):
    # Initialize the lists of deposits, withdrawals, and incomes
    self.withdrawals = []
    self.deposits = []
    self.incomes = []
    self.tax_receipts = []

    self.year = world.BASE_YEAR
    self.growth_rate = 0
    self.age = world.START_AGE
    self.rrsp_room = 0
    self.tfsa_room = 0

    self.is_dead = False
    self.is_employed = False
    self.is_retired = False

LifetimeRecord = collections.namedtuple('LifetimeRecord',
    [])

def Indexed(base, current_year, rate=1+world.PARGE):
  return base * (rate ** (current_year - world.BASE_YEAR))

class SummaryStatsAccumulator(object):
  """This uses a generalization of Welford's Algorithm by Chan et al [1] to
  calculate mean, variance, and standard deviation in one pass, with the ability
  to update from intermediate objects of this class as well as from single
  data points.

  [1] http://i.stanford.edu/pub/cstr/reports/cs/tr/79/773/CS-TR-79-773.pdf
  """
  def __init__(self):
    self.n = 0
    self.mean = 0
    self.M2 = 0

  def UpdateOneValue(self, value):
    self.n += 1
    delta = value - self.mean
    self.mean += delta / self.n
    self.M2 += delta * (value - self.mean)

  def UpdateSubsample(self, n, mean, M2):
    delta = mean - self.mean
    self.mean = (self.mean * self.n + mean * n) / (self.n + n)
    self.M2 += M2 + math.pow(delta, 2) * self.n * n / (self.n + n)
    self.n += n

  @property
  def variance(self):
    """Returns the sample variance, or NaN if fewer than 2 updates."""
    if self.n > 1:
      return self.M2 / (self.n - 1)
    else:
      return float('nan')

  @property
  def stddev(self):
    """Returns the sample standard deviation, or NaN if fewer than 2 updates."""
    return math.sqrt(self.variance)


class QuantileAccumulator(object):
  """This uses a streaming parallel histogram building algorithm described by
  Ben-Haim and Yom-Tov in [1] to accumulate values, and uses this histogram to
  provide quantile approximations.

  [1] http://jmlr.org/papers/volume11/ben-haim10a/ben-haim10a.pdf
  """
  def __init__(self, max_bins=100):
    self.max_bins = max_bins
    self.bins = []

  def _Merge(self):
    """Merges bins if there are more than max_bins. Expects self.bins to be sorted"""
    while len(self.bins) > self.max_bins:
      # Find the two closest bins
      sep, i = min((self.bins[i+1][0] - self.bins[i][0], i) for i in range(len(self.bins)-1))

      # Merge them
      self.bins[i:i+2] = [(
          (self.bins[i][0]*self.bins[i][1] + self.bins[i+1][0]*self.bins[i+1][1])/(self.bins[i][1]+self.bins[i+1][1]),
          self.bins[i][1]+self.bins[i+1][1])]

  def UpdateOneValue(self, value):
    bisect.insort(self.bins, (value, 1))
    self._Merge()

  def UpdateHistogram(self, bins):
    self.bins.extend(bins)
    self.bins.sort()
    self._Merge()

  def Quantile(self, q):
    if q < 0 or 1 < q:
      raise ValueError("quantile should be a number between 0 and 1, inclusive")

    # Cumulative sum of the counts at each bin point, treating the point as the center of the bin
    bin_counts = [0] + [b[1] for b in self.bins] + [0]
    cumsums = [0]
    for i in range(1, len(bin_counts)):
      bin_count = (bin_counts[i] + bin_counts[i-1])/2
      cumsums.append(cumsums[-1] + bin_count)

    # Find the index of the interval in which the desired quantile lies
    n_points = q * cumsums[-1]
    i = bisect.bisect(cumsums, n_points)-1

    if i <= 0:
      # special case, quantile falls before first bin
      return self.bins[0][0]
    elif i >= len(self.bins):
      # Special case, quantile falls at or after last bin
      return self.bins[-1][0]
    else:
      bin_frac = (n_points - cumsums[i])/(cumsums[i+1] - cumsums[i])
      return self.bins[i-1][0] + bin_frac * (self.bins[i][0] - self.bins[i-1][0])

    
