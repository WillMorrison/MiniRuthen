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
    self.growth_records = []

    self.year = world.BASE_YEAR
    self.growth_rate = 0
    self.age = world.START_AGE
    self.cpi = 1
    self.inflation = 0
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
    if not (self.n or n):
      return
    delta = mean - self.mean
    self.mean = (self.mean * self.n + mean * n) / (self.n + n)
    self.M2 += M2 + math.pow(delta, 2) * self.n * n / (self.n + n)
    self.n += n

  def UpdateAccumulator(self, acc):
    self.UpdateSubsample(acc.n, acc.mean, acc.M2)

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

  @property
  def stderr(self):
    """Returns the standard error, or NaN if fewer than 2 updates."""
    if self.n:
      return math.sqrt(self.variance/self.n)
    else:
      return float('nan')

  @property
  def total(self):
    return self.n * self.mean


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

    # Merge bins with identical centroids first, regardless of self.max_bins
    zero_diffs = [(self.bins[i+1][0] - self.bins[i][0], i) for i in range(len(self.bins)-1) if not self.bins[i+1][0] - self.bins[i][0]]
    for _, i in reversed(zero_diffs):
      self.bins[i:i+2] = [(self.bins[i][0], self.bins[i][1]+self.bins[i+1][1])]

    # Now merge other bins until we have at most self.max_bins
    diffs = [(self.bins[i+1][0] - self.bins[i][0], i) for i in range(len(self.bins)-1)]
    removed = []
    while len(self.bins) > self.max_bins:
      # Find the two closest bins
      sep, i = min(diffs)
      i_adjustment = bisect.bisect_left(removed, i)
      removed.insert(i_adjustment, i)
      i -= i_adjustment

      # Merge them
      self.bins[i:i+2] = [(
          (self.bins[i][0]*self.bins[i][1] + self.bins[i+1][0]*self.bins[i+1][1])/(self.bins[i][1]+self.bins[i+1][1]),
          self.bins[i][1]+self.bins[i+1][1])]
      if i:
        diffs[i-1:i+1] = [(self.bins[i][0] - self.bins[i-1][0], diffs[i-1][1])]
      else:
        diffs[0:2] = [(self.bins[1][0] - self.bins[0][0], diffs[1][1])]

  def UpdateOneValue(self, value):
    bisect.insort_left(self.bins, (value, 1))
    self._Merge()

  def UpdateHistogram(self, bins):
    self.bins.extend(bins)
    self.bins.sort()
    self._Merge()

  def UpdateAccumulator(self, acc):
    self.UpdateHistogram(acc.bins)

  def Quantile(self, q):
    if q < 0 or 1 < q:
      raise ValueError("quantile should be a number between 0 and 1, inclusive")

    if len(self.bins) == 0:
      return float('nan')

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


class PicklableLambda(object):
  """cPickle is dumb, but we need lambdas."""
  def __init__(self, callable_object, args=None):
    self.callable_object = callable_object
    self.args = args or {}

  def __call__(self):
    return self.callable_object(**self.args)


class KeyedAccumulator(object):
  """Keeps track of subaccumulators by key and allows querying."""

  def __init__(self, subaccumulator_class, subaccumulator_args=None):
    self.default_factory = PicklableLambda(subaccumulator_class, subaccumulator_args)
    self._accumulators = collections.defaultdict(self.default_factory)

  def UpdateOneValue(self, value, key):
    self._accumulators[key].UpdateOneValue(value)

  def UpdateAccumulator(self, acc):
    for key in acc._accumulators:
      self._accumulators[key].UpdateAccumulator(acc._accumulators[key])

  def Query(self, keys):
    """Returns an accumulator resulting from the merge of all subaccumulators with the given keys."""
    result = self.default_factory()
    default = self.default_factory()
    for key in keys:
      result.UpdateAccumulator(self._accumulators.get(key, default))
    return result        


class AccumulatorBundle(object):
  def __init__(self, basic_only=False):
    # Accumulators needed for fitness function
    self.lifetime_consumption_summary = SummaryStatsAccumulator()
    self.lifetime_consumption_hist = QuantileAccumulator()
    self.working_consumption_summary = SummaryStatsAccumulator()
    self.working_consumption_hist = QuantileAccumulator()
    self.retired_consumption_summary = SummaryStatsAccumulator()
    self.retired_consumption_hist = QuantileAccumulator()
    self.pre_disability_retired_consumption_summary = SummaryStatsAccumulator()
    self.discounted_lifetime_consumption_summary = SummaryStatsAccumulator()
    self.earnings_late_working_summary = SummaryStatsAccumulator()
    self.fraction_persons_ruined = SummaryStatsAccumulator()
    self.fraction_retirement_years_ruined = SummaryStatsAccumulator()
    self.fraction_retirement_years_below_ympe = SummaryStatsAccumulator()
    self.fraction_retirement_years_below_twice_ympe = SummaryStatsAccumulator()
    self.fraction_retirees_receiving_gis = SummaryStatsAccumulator()
    self.fraction_retirement_years_receiving_gis = SummaryStatsAccumulator()
    self.benefits_gis = SummaryStatsAccumulator()
    self.fraction_retirees_ever_below_lico = SummaryStatsAccumulator()
    self.fraction_retirement_years_below_lico = SummaryStatsAccumulator()
    self.lico_gap_working = SummaryStatsAccumulator()
    self.lico_gap_retired = SummaryStatsAccumulator()
    self.fraction_persons_with_withdrawals_below_retirement_assets = SummaryStatsAccumulator()
    self.fraction_retirees_with_withdrawals_below_retirement_assets = SummaryStatsAccumulator()
    self.lifetime_withdrawals_less_savings = SummaryStatsAccumulator()
    self.retirement_consumption_less_working_consumption = SummaryStatsAccumulator()
    self.distributable_estate = SummaryStatsAccumulator()

    if basic_only:
      return

    # Accumulators needed for summary table
    self.age_at_death = SummaryStatsAccumulator()
    self.years_worked_with_earnings = SummaryStatsAccumulator()
    self.earnings_working = SummaryStatsAccumulator()
    self.fraction_persons_involuntarily_retired = SummaryStatsAccumulator()
    self.fraction_persons_dying_before_retiring = SummaryStatsAccumulator()
    self.working_annual_ei_cpp_deductions = SummaryStatsAccumulator()
    self.working_taxes = SummaryStatsAccumulator()
    self.retirement_taxes = SummaryStatsAccumulator()
    self.positive_savings_years = SummaryStatsAccumulator()
    self.fraction_earnings_saved = SummaryStatsAccumulator()
    self.years_receiving_ei = SummaryStatsAccumulator()
    self.positive_ei_benefits = SummaryStatsAccumulator()
    self.years_receiving_gis = SummaryStatsAccumulator()
    self.positive_gis_benefits = SummaryStatsAccumulator()
    self.positive_cpp_benefits = SummaryStatsAccumulator()
    self.years_income_below_lico = SummaryStatsAccumulator()
    self.years_with_no_assets = SummaryStatsAccumulator()
    self.years_with_negative_consumption = SummaryStatsAccumulator()

    # Accumulators for period specific tables
    self.period_years = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_earnings = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_cpp_benefits = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_oas_benefits = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_taxable_gains = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_gis_benefits = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_social_benefits_repaid = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_rrsp_withdrawals = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_tfsa_withdrawals = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_nonreg_withdrawals = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_cpp_contributions = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_ei_premiums = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_taxable_income = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_income_tax = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_sales_tax = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_consumption = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_rrsp_savings = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_tfsa_savings = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_nonreg_savings = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_fund_growth = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_gross_estate = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_estate_taxes = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_executor_funeral_costs = KeyedAccumulator(SummaryStatsAccumulator)
    self.period_distributable_estate = KeyedAccumulator(SummaryStatsAccumulator)

    # Accumulators for age specific table
    self.persons_alive_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.gross_earnings_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.income_tax_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.sales_tax_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.ei_premium_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.cpp_contributions_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.ei_benefits_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.cpp_benefits_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.oas_benefits_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.gis_benefits_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.savings_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.rrsp_withdrawals_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.tfsa_withdrawals_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.nonreg_withdrawals_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.consumption_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.consumption_hist_by_age = KeyedAccumulator(QuantileAccumulator)
    self.rrsp_assets_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.bridging_assets_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.tfsa_assets_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.nonreg_assets_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.ced_withdrawals_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    self.cd_withdrawals_by_age = KeyedAccumulator(SummaryStatsAccumulator)
    
  def UpdateConsumption(self, consumption, year, is_retired, period):
    discounted_consumption = Indexed(consumption, year, 1-world.DISCOUNT_RATE)
    age = year - world.BASE_YEAR + world.START_AGE

    self.lifetime_consumption_summary.UpdateOneValue(consumption)
    self.lifetime_consumption_hist.UpdateOneValue(consumption)
    self.discounted_lifetime_consumption_summary.UpdateOneValue(discounted_consumption)
    self.years_with_negative_consumption.UpdateOneValue(1 if consumption < 0 else 0)
    if is_retired:
      self.retired_consumption_summary.UpdateOneValue(consumption)
      self.retired_consumption_hist.UpdateOneValue(consumption)
      if age <= world.AVG_DISABILITY_AGE:
        self.pre_disability_retired_consumption_summary.UpdateOneValue(consumption)
    else:
      self.working_consumption_summary.UpdateOneValue(consumption)
      self.working_consumption_hist.UpdateOneValue(consumption)
    if hasattr(self, 'consumption_by_age'):
      self.consumption_by_age.UpdateOneValue(consumption, age)
      self.consumption_hist_by_age.UpdateOneValue(consumption, age)
      self.period_consumption.UpdateOneValue(consumption, period)

  def Merge(self, bundle):
    """Merge in another AccumulatorBundle."""
    for attr in self.__dict__:
      getattr(self, attr).UpdateAccumulator(getattr(bundle, attr))
