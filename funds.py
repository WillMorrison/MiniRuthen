""" This module contains code related to Funds in miniRuthen."""

import collections
import utils
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
TaxReceipt = collections.namedtuple('TaxReceipt', ('gross_gain', 'fund_type'))


class Fund(object):

  def __init__(self):
    self.fund_type = FUND_TYPE_NONE
    self.amount = 0
    self.room_replenishes = False
    self.unrealized_gains = 0
    self.forced_withdraw = 0
  
  def Deposit(self, amount, year_rec):
    room = self.GetRoom(year_rec)
    if room == NO_ROOM_LIMIT:
      self.amount += amount
      deposited = amount
    else:
      if room >= amount:
        self.amount += amount
        room -= amount
        deposited = amount
      else:
        deposited = room
        self.amount += deposited
        room = 0
    year_rec.deposits.append(DepositReceipt(deposited, self.fund_type))
    self.SetRoom(year_rec, room)
    return (deposited, year_rec)

  def Withdraw(self, amount, year_rec):
    room = self.GetRoom(year_rec)
    try:
      gain_proportion = self.unrealized_gains / self.amount
    except ZeroDivisionError:
      gain_proportion = 0

    if self.forced_withdraw > amount:
      amount = self.forced_withdraw

    if self.amount >= amount:
      withdrawn = amount
      self.amount -= amount
    else:
      withdrawn = self.amount
      self.amount = 0
    
    if room != NO_ROOM_LIMIT and self.room_replenishes:
      room += withdrawn

    self.forced_withdraw = 0

    realized_gains = withdrawn * gain_proportion
    self.unrealized_gains -= realized_gains

    year_rec.withdrawals.append(WithdrawReceipt(withdrawn, realized_gains, self.fund_type))
    self.SetRoom(year_rec, room)
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

  def GetRoom(self, year_rec):
    return NO_ROOM_LIMIT

  def SetRoom(self, year_rec, room):
    pass

class TFSA(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_TFSA
    self.room_replenishes = True

  def Update(self, year_rec):
    self.amount += self.Growth(year_rec)

  def GetRoom(self, year_rec):
    return year_rec.tfsa_room

  def SetRoom(self, year_rec, room):
    year_rec.tfsa_room = room


class RRSP(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_RRSP
    self.room = world.RRSP_INITIAL_LIMIT

  def Update(self, year_rec):
    # RRSP new room calculation TODO move this logic to person
    # earning_receipts = [receipt for receipt in year_rec.incomes
    #                     if receipt.income_type == incomes.INCOME_TYPE_EARNINGS]
    # earnings_total = sum(receipt.amount for receipt in earning_receipts)
    # self.room += min(utils.Indexed(world.RRSP_LIMIT, year_rec.year), world.RRSP_ACCRUAL_FRACTION * earnings_total)

    # Growth
    self.amount += self.Growth(year_rec)

    # calculate RRSP mandatory withdrawal
    self.forced_withdraw = world.MINIMUM_WITHDRAWAL_FRACTION[year_rec.age+1] * self.amount

  def GetRoom(self, year_rec):
    return year_rec.rrsp_room

  def SetRoom(self, year_rec, room):
    year_rec.rrsp_room = room


class NonRegistered(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_NONREG
  
  def Update(self, year_rec):
    growth = self.Growth(year_rec)
    self.amount += growth
    realized_gains = world.UNREALIZED_GAINS_REALIZATION_FRACTION * self.unrealized_gains
    self.unrealized_gains -= realized_gains
    new_realized_gains = growth * world.IMMEDIATELY_REALIZED_GAINS_FRACTION
    year_rec.tax_receipts.append(TaxReceipt(realized_gains + new_realized_gains, self.fund_type))
    self.unrealized_gains += growth - new_realized_gains


class RRSPBridging(Fund):

  def __init__(self):
    super().__init__()
    self.fund_type = FUND_TYPE_BRIDGING

  def Deposit(self, amount, year_rec):
    deposited = 0 # No deposits allowed after account creation
    year_rec.deposits.append(DepositReceipt(deposited, self.fund_type))
    return (deposited, year_rec)


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

def SplitFund(source, sink, amount):
  """Partition a fund into two pieces, transferring gains as appropriate."""
  if source.amount == 0:
    return (source, sink)
  amount_to_move = min(amount, source.amount)
  unrealized_gains_to_move = source.unrealized_gains * amount_to_move / source.amount
  source.amount -= amount_to_move
  sink.amount += amount_to_move
  source.unrealized_gains -= unrealized_gains_to_move
  sink.unrealized_gains += unrealized_gains_to_move
  return (source, sink)

