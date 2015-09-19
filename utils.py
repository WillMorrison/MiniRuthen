"""Utils holds miscellaneous classes and functions that don't fit elsewhere."""

import world
import collections

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
