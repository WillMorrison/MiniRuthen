""" This module contains code related to Funds in miniRuthen."""

import collections
import world
import incomes

# Special value indicating fund has no cap on deposits
NO_ROOM_LIMIT = "No limit"

# Types of funds, used in receipts
FUND_TYPE_NONE = "Generic Fund"
FUND_TYPE_TFSA = "TFSA"
FUND_TYPE_RRSP = "RRSP"
FUND_TYPE_NONREG = "Non Registered"
FUND_TYPE_BRIDGING = "RRSP Bridging"


# Receipts go into year records
DepositReceipt = collections.namedtuple('DepositReceipt', ('amount', 'fund_type'))
WithdrawReceipt = collections.namedtuple('WithdrawReceipt', ('amount', 'gains', 'fund_type'))


class Fund(object):

  def __init__(self):
    self.fund_type = FUND_TYPE_NONE
    self.amount = 0
    self.room = NO_ROOM_LIMIT
    self.room_replenishes = False
    self.unrealized_gains = 0
    self.forced_withdraw = 0
  
  def Deposit(self, amount, year_rec):
    if self.room == NO_ROOM_LIMIT:
      self.amount += amount
      deposited = amount
    else:
      if self.room >= amount:
        self.amount += amount
        self.room -= amount
        deposited = amount
      else:
        deposited = self.room
        self.amount += deposited
        self.room = 0
    year_rec.deposits.append(DepositReceipt(deposited, self.fund_type))
    return (deposited, year_rec)

  def Withdraw(self, amount, year_rec):
    gain_proportion = self.unrealized_gains / self.amount

    if self.forced_withdraw > amount:
      amount = self.forced_withdraw

    if self.amount >= amount:
      withdrawn = amount
      self.amount -= amount
    else:
      withdrawn = self.amount
      self.amount = 0
    
    if self.room != NO_ROOM_LIMIT and self.room_replenishes:
      self.room += withdrawn

    self.forced_withdraw = 0

    realized_gains = withdrawn * gain_proportion
    self.unrealized_gains -= realized_gains

    year_rec.withdrawals.append(WithdrawReceipt(withdrawn, realized_gains, self.fund_type))
    return (withdrawn, realized_gains, year_rec)

  def Update(self, year_rec):
    pass

  def Growth(self, year_rec):
    """Calculates the amount to be added to the fund based on the growth rate.
    The growth rate is 0 if the fund does not change, positive if it should
    grow, and negative if it should shrink. Regardless of the rate, Growth()
    will not return a number so negative it would cause the fund amount to go
    negative.
    """
    return max(self.amount * year_rec.growth_rate, -self.amount)

class TFSA(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_TFSA
    self.room = world.TFSA_INITIAL_CONTRIBUTION_LIMIT
    self.room_replenishes = True

  def Update(self, year_rec):
    self.room += world.TFSA_ANNUAL_CONTRIBUTION_LIMIT
    self.amount += self.Growth(year_rec)


class RRSP(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_RRSP
    self.room = world.RRSP_INITIAL_LIMIT

  def Update(self, year_rec):
    # RRSP new room calculation
    earning_receipts = [receipt for receipt in year_rec.incomes
                        if receipt.income_type == incomes.INCOME_TYPE_EARNINGS]
    earnings_total = sum(receipt.amount for receipt in earning_receipts)
    self.room += min(world.RRSP_LIMIT, world.RRSP_ACCRUAL_FRACTION * earnings_total)

    # Growth
    self.amount += self.Growth(year_rec)

    # calculate RRSP mandatory withdrawal
    self.forced_withdraw = world.MINIMUM_WITHDRAWAL_FRACTION[year_rec.age+1] * self.amount


class NonRegistered(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_NONREG
  
  def Update(self, year_rec):
    growth = self.Growth(year_rec)
    self.amount += growth
    self.unrealized_gains += max(growth, -self.unrealized_gains)


class RRSPBridging(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_BRIDGING
    self.room = 0  # No deposits allowed after account creation


def ChainedDeposit(amount, funds, proportions, year_rec):
  total_withdrawn, _, year_rec = ChainedTransaction(
    -amount, funds, proportions, proportions, year_rec)
  return (-total_withdrawn, year_rec)

def ChainedWithdraw(amount, funds, proportions, year_rec):
  withdrawn, realized_gains, year_rec = ChainedTransaction(
      amount, funds, proportions, proportions, year_rec)
  return (withdrawn, realized_gains, year_rec)

def ChainedTransaction(amount, funds, withdrawal_proportions,
                       deposit_proportions, year_rec):
  total_withdrawn = 0
  total_realized_gains = 0

  for fund, withdrawal_proportion, deposit_proportion in zip(funds, withdrawal_proportions, deposit_proportions):
    if total_withdrawn < amount:
      to_withdraw = (amount - total_withdrawn) * withdrawal_proportion
      withdrawn, realized_gains, year_rec = fund.Withdraw(to_withdraw,
                                                          year_rec)
      total_withdrawn += withdrawn
      total_realized_gains += realized_gains
    elif total_withdrawn > amount:
      to_deposit = (total_withdrawn - amount) * deposit_proportion
      deposited, year_rec = fund.Deposit(to_deposit, year_rec)
      total_withdrawn -= deposited
    else:
      break
  return (total_withdrawn, total_realized_gains, year_rec)
