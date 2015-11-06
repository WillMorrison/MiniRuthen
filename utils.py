"""Utils holds miscellaneous classes and functions that don't fit elsewhere."""

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
