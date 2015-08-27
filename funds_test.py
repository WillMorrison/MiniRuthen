import unittest
import funds
import utils
import world
import incomes

class FundTest(unittest.TestCase):

  def testDepositUnlimitedRoom(self):
    fund = funds.Fund()
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_NONE),
                  year_rec.deposits)

  def testDepositSufficientRoom(self):
    fund = funds.Fund()
    fund.room = 20
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_NONE),
                  year_rec.deposits)
    self.assertEqual(fund.room, 5)

  def testDepositInsufficientRoom(self):
    fund = funds.Fund()
    fund.room = 10
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 10)
    self.assertEqual(fund.amount, 10)
    self.assertIn(funds.DepositReceipt(10, funds.FUND_TYPE_NONE),
                  year_rec.deposits)
    self.assertEqual(fund.room, 0)
    
  def testWithdrawSufficientFunds(self):
    fund = funds.Fund()
    fund.amount = 20
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_NONE),
                  year_rec.withdrawals)

  def testWithdrawInsufficientFunds(self):
    fund = funds.Fund()
    fund.amount = 5
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 5)
    self.assertEqual(fund.amount, 0)
    self.assertIn(funds.WithdrawReceipt(5, 0, funds.FUND_TYPE_NONE),
                  year_rec.withdrawals)

  def testWithdrawRealizedGains(self):
    fund = funds.Fund()
    fund.amount = 40
    fund.unrealized_gains = 5
    withdrawn, gains, year_rec = fund.Withdraw(10, utils.YearRecord())
    self.assertEqual(withdrawn, 10)
    self.assertEqual(gains, 1.25)
    self.assertEqual(fund.unrealized_gains, 3.75)
    self.assertIn(funds.WithdrawReceipt(10, 1.25, funds.FUND_TYPE_NONE),
                  year_rec.withdrawals)

  def testWithdrawRoomReplenishment(self):
    fund = funds.Fund()
    fund.amount = 20
    fund.room = 5
    fund.room_replenishes = True
    withdrawn, gains, year_rec = fund.Withdraw(10, utils.YearRecord())
    self.assertEqual(fund.room, 15)

  def testWithdrawForcedPassive(self):
    fund = funds.Fund()
    fund.amount = 20
    fund.forced_withdraw = 5
    withdrawn, gains, year_rec = fund.Withdraw(10, utils.YearRecord())
    self.assertEqual(withdrawn, 10)
    self.assertEqual(fund.amount, 10)
    self.assertEqual(fund.forced_withdraw, 0)

  def testWithdrawForcedActive(self):
    fund = funds.Fund()
    fund.amount = 20
    fund.forced_withdraw = 15
    withdrawn, gains, year_rec = fund.Withdraw(10, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertEqual(fund.forced_withdraw, 0)

  def testWithdrawForcedInsufficient(self):
    fund = funds.Fund()
    fund.amount = 10
    fund.forced_withdraw = 15
    withdrawn, gains, year_rec = fund.Withdraw(5, utils.YearRecord())
    self.assertEqual(withdrawn, 10)
    self.assertEqual(fund.amount, 0)
    self.assertEqual(fund.forced_withdraw, 0)

  def testGrowthZero(self):
    fund = funds.Fund()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0
    self.assertEqual(fund.Growth(year_rec), 0)

  def testGrowthPositive(self):
    fund = funds.Fund()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.1
    self.assertEqual(fund.Growth(year_rec), 2)

  def testGrowthNegative(self):
    fund = funds.Fund()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -0.1
    self.assertEqual(fund.Growth(year_rec), -2)

  def testGrowthVeryNegative(self):
    fund = funds.Fund()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -1.2
    self.assertEqual(fund.Growth(year_rec), -20)


class TFSATest(unittest.TestCase):

  def testTFSARoom(self):
    fund = funds.TFSA()
    self.assertEqual(fund.room, world.TFSA_INITIAL_CONTRIBUTION_LIMIT)
    fund.Update(utils.YearRecord())
    self.assertEqual(fund.room, (world.TFSA_INITIAL_CONTRIBUTION_LIMIT +
                                 world.TFSA_ANNUAL_CONTRIBUTION_LIMIT))

  def testTFSADeposit(self):
    fund = funds.TFSA()
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_TFSA),
                  year_rec.deposits)
  
  def testTFSAWithdraw(self):
    fund = funds.TFSA()
    fund.amount = 20
    fund.room = 0
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_TFSA),
                  year_rec.withdrawals)
    self.assertEqual(fund.room, 15)

  def testTFSAUpdate(self):
    fund = funds.TFSA()
    fund.amount = 20
    fund.room = 0
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.2
    fund.Update(year_rec)
    self.assertEqual(fund.room, world.TFSA_ANNUAL_CONTRIBUTION_LIMIT)
    self.assertEqual(fund.amount, 24)
    self.assertEqual(fund.unrealized_gains, 0)


class RRSPTest(unittest.TestCase):

  def testRRSPRoom(self):
    fund = funds.RRSP()
    year_rec = utils.YearRecord()
    year_rec.incomes.append(incomes.IncomeReceipt(10000, incomes.INCOME_TYPE_EARNINGS))
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT)
    fund.Update(year_rec)
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT+1800)

  def testRRSPRoomLimit(self):
    fund = funds.RRSP()
    year_rec = utils.YearRecord()
    year_rec.incomes.append(incomes.IncomeReceipt(140000, incomes.INCOME_TYPE_EARNINGS))
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT)
    fund.Update(year_rec)
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT+world.RRSP_LIMIT)

  def testRRSPDeposit(self):
    fund = funds.RRSP()
    fund.room = 20
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_RRSP),
                  year_rec.deposits)
    self.assertEqual(fund.room, 5)
  
  def testRRSPWithdraw(self):
    fund = funds.RRSP()
    fund.amount = 20
    fund.room = 0
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_RRSP),
                  year_rec.withdrawals)
    self.assertEqual(fund.room, 0)

  def testRRSPForcedWithdrawEarly(self):
    fund = funds.RRSP()
    fund.amount = 10000
    year_rec = utils.YearRecord()
    year_rec.age = 69
    fund.Update(year_rec)
    self.assertEqual(fund.forced_withdraw, 0)

  def testRRSPForcedWithdrawActive(self):
    fund = funds.RRSP()
    fund.amount = 10000
    year_rec = utils.YearRecord()
    year_rec.age = 70
    fund.Update(year_rec)
    self.assertEqual(fund.forced_withdraw, 528)

  def testRRSPUpdate(self):
    fund = funds.RRSP()
    fund.amount = 20
    fund.room = 0
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.2
    year_rec.incomes.append(incomes.IncomeReceipt(10000, incomes.INCOME_TYPE_EARNINGS))
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 24)
    self.assertEqual(fund.room, 1800)
    self.assertEqual(fund.unrealized_gains, 0)


class NonRegisteredTest(unittest.TestCase):

  def testNonRegisteredDeposit(self):
    fund = funds.NonRegistered()
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_NONREG),
                  year_rec.deposits)
    self.assertEqual(fund.room, funds.NO_ROOM_LIMIT)
    self.assertEqual(fund.unrealized_gains, 0)
  
  def testNonRegisteredWithdraw(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertEqual(fund.unrealized_gains, 2.5)
    self.assertIn(funds.WithdrawReceipt(15, 7.5, funds.FUND_TYPE_NONREG),
                  year_rec.withdrawals)

  def testNonRegisteredUpdate(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.2
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 24)
    self.assertEqual(fund.unrealized_gains, 14)

  def testNonRegisteredUpdateGainsDecrement(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -0.2
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 16)
    self.assertEqual(fund.unrealized_gains, 6)

  def testNonRegisteredUpdateGainsDecrementToZero(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -0.6
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 8)
    self.assertEqual(fund.unrealized_gains, 0)


class RRSPBridgingTest(unittest.TestCase):

  def testRRSPBridgingDeposit(self):
    fund = funds.RRSPBridging()
    fund.amount = 30
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 0)
    self.assertEqual(fund.amount, 30)
    self.assertIn(funds.DepositReceipt(0, funds.FUND_TYPE_BRIDGING),
                  year_rec.deposits)
    self.assertEqual(fund.room, 0)
  
  def testRRSPBridgingWithdraw(self):
    fund = funds.RRSPBridging()
    fund.amount = 20
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertEqual(fund.unrealized_gains, 0)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_BRIDGING),
                  year_rec.withdrawals)
    self.assertEqual(fund.room, 0)


class ChainingTest(unittest.TestCase):
  
  def testChainedDeposit(self):
    tfsa = funds.TFSA()
    tfsa.room = 30
    rrsp = funds.RRSP()
    rrsp.room = 50
    bridging = funds.RRSPBridging()
    bridging.amount = 60
    nonreg = funds.NonRegistered()
    fund_chain = (tfsa, rrsp, bridging, nonreg)
    proportions = (1, 1, 1, 1)
    deposited, year_rec = funds.ChainedDeposit(100, fund_chain, proportions,
                                               utils.YearRecord())
    self.assertEqual(deposited, 100)
    self.assertSequenceEqual(year_rec.deposits,
                            [funds.DepositReceipt(30, funds.FUND_TYPE_TFSA),
                             funds.DepositReceipt(50, funds.FUND_TYPE_RRSP),
                             funds.DepositReceipt(0, funds.FUND_TYPE_BRIDGING),
                             funds.DepositReceipt(20, funds.FUND_TYPE_NONREG)])
    self.assertEqual(tfsa.amount, 30)
    self.assertEqual(rrsp.amount, 50)
    self.assertEqual(bridging.amount, 60)
    self.assertEqual(nonreg.amount, 20)
                             
  def testChainedDepositInsufficientRoom(self):
    tfsa = funds.TFSA()
    tfsa.room = 30
    rrsp = funds.RRSP()
    rrsp.room = 50
    fund_chain = (tfsa, rrsp)
    proportions = (1, 1)
    deposited, year_rec = funds.ChainedDeposit(100, fund_chain, proportions,
                                               utils.YearRecord())
    self.assertEqual(deposited, 80)
    self.assertSequenceEqual(year_rec.deposits,
                             [funds.DepositReceipt(30, funds.FUND_TYPE_TFSA),
                              funds.DepositReceipt(50, funds.FUND_TYPE_RRSP)])
    self.assertEqual(tfsa.amount, 30)
    self.assertEqual(rrsp.amount, 50)
                             
  def testChainedDepositProportions(self):
    tfsa = funds.TFSA()
    tfsa.room = 30
    rrsp = funds.RRSP()
    rrsp.room = 30
    nonreg = funds.NonRegistered()
    fund_chain = (tfsa, rrsp, nonreg)
    proportions = (0.2, 0.5, 1)
    deposited, year_rec = funds.ChainedDeposit(100, fund_chain, proportions,
                                               utils.YearRecord())
    self.assertEqual(deposited, 100)
    self.assertSequenceEqual(year_rec.deposits,
                             [funds.DepositReceipt(20, funds.FUND_TYPE_TFSA),
                              funds.DepositReceipt(30, funds.FUND_TYPE_RRSP),
                              funds.DepositReceipt(50, funds.FUND_TYPE_NONREG)])
    self.assertEqual(tfsa.amount, 20)
    self.assertEqual(rrsp.amount, 30)
    self.assertEqual(nonreg.amount, 50)

  def testChainedWithdrawSufficientFunds(self):
    rrsp = funds.RRSP()
    rrsp.amount = 20
    tfsa = funds.TFSA()
    tfsa.amount = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 30
    nonreg.unrealized_gains = 15
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 60)
    self.assertEqual(gains, 13.5)
    self.assertSequenceEqual(
        year_rec.withdrawals, 
        [funds.WithdrawReceipt(6, 0, funds.FUND_TYPE_RRSP),
         funds.WithdrawReceipt(27, 0, funds.FUND_TYPE_TFSA),
         funds.WithdrawReceipt(27, 13.5, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 14)
    self.assertEqual(tfsa.amount, 23)
    self.assertEqual(nonreg.amount, 3)
    self.assertEqual(nonreg.unrealized_gains, 1.5)

  def testChainedWithdrawInsufficientFunds(self):
    # TODO check if this is correct behaviour, or if we need more complicated
    # logic for insufficient funds at the end of the chain
    rrsp = funds.RRSP()
    rrsp.amount = 20
    tfsa = funds.TFSA()
    tfsa.amount = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 20
    nonreg.unrealized_gains = 10
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 53)
    self.assertEqual(gains, 10)
    self.assertSequenceEqual(
        year_rec.withdrawals, 
        [funds.WithdrawReceipt(6, 0, funds.FUND_TYPE_RRSP),
         funds.WithdrawReceipt(27, 0, funds.FUND_TYPE_TFSA),
         funds.WithdrawReceipt(20, 10, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 14)
    self.assertEqual(tfsa.amount, 23)
    self.assertEqual(nonreg.amount, 0)

  def testChainedWithdrawPartialInsufficientFunds(self):
    rrsp = funds.RRSP()
    rrsp.amount = 20
    tfsa = funds.TFSA()
    tfsa.amount = 20
    nonreg = funds.NonRegistered()
    nonreg.amount = 40
    nonreg.unrealized_gains = 20
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 60)
    self.assertEqual(gains, 17)
    self.assertSequenceEqual(
        year_rec.withdrawals, 
        [funds.WithdrawReceipt(6, 0, funds.FUND_TYPE_RRSP),
         funds.WithdrawReceipt(20, 0, funds.FUND_TYPE_TFSA),
         funds.WithdrawReceipt(34, 17, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 14)
    self.assertEqual(tfsa.amount, 0)
    self.assertEqual(nonreg.amount, 6)

  def testChainedWithdrawForcedWithdraw(self):
    rrsp = funds.RRSP()
    rrsp.amount = 20
    rrsp.forced_withdraw = 10
    tfsa = funds.TFSA()
    tfsa.amount = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 30
    nonreg.unrealized_gains = 15
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 60)
    self.assertEqual(gains, 12.5)
    self.assertSequenceEqual(
        year_rec.withdrawals, 
        [funds.WithdrawReceipt(10, 0, funds.FUND_TYPE_RRSP),
         funds.WithdrawReceipt(25, 0, funds.FUND_TYPE_TFSA),
         funds.WithdrawReceipt(25, 12.5, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 10)
    self.assertEqual(tfsa.amount, 25)
    self.assertEqual(nonreg.amount, 5)

  def testChainedWithdrawForcedWithdrawProportionalDeposit(self):
    rrsp = funds.RRSP()
    rrsp.amount = 100
    rrsp.forced_withdraw = 80
    tfsa = funds.TFSA()
    tfsa.amount = 50
    tfsa.room = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 50
    nonreg.unrealized_gains = 25
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 60)
    self.assertEqual(gains, 0)
    self.assertSequenceEqual(
        year_rec.withdrawals, 
        [funds.WithdrawReceipt(80, 0, funds.FUND_TYPE_RRSP)])
    self.assertSequenceEqual(
        year_rec.deposits,
        [funds.DepositReceipt(10, funds.FUND_TYPE_TFSA),
         funds.DepositReceipt(10, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 20)
    self.assertEqual(tfsa.amount, 60)
    self.assertEqual(nonreg.amount, 60)

  def testChainedWithdrawForcedWithdrawOverflow(self):
    rrsp = funds.RRSP()
    rrsp.amount = 100
    rrsp.forced_withdraw = 80
    tfsa = funds.TFSA()
    tfsa.amount = 50
    tfsa.room = 0
    fund_chain = (rrsp, tfsa)
    proportions = (0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 80)
    self.assertEqual(gains, 0)
    self.assertSequenceEqual(
        year_rec.withdrawals,
        [funds.WithdrawReceipt(80, 0, funds.FUND_TYPE_RRSP)])
    self.assertSequenceEqual(
        year_rec.deposits, [funds.DepositReceipt(0, funds.FUND_TYPE_TFSA)])
    self.assertEqual(rrsp.amount, 20)
    self.assertEqual(tfsa.amount, 50)

  def testChainedTransactionDifferentProportion(self):
    rrsp = funds.RRSP()
    rrsp.amount = 100
    rrsp.forced_withdraw = 80
    tfsa = funds.TFSA()
    tfsa.amount = 50
    nonreg = funds.NonRegistered()
    fund_chain = (rrsp, tfsa, nonreg)
    withdrawal_proportions = (0.5, 0.5, 1)
    deposit_proportions = (0.5, 0.8, 1)
    withdrawn, gains, year_rec = funds.ChainedTransaction(
        60, fund_chain, withdrawal_proportions, deposit_proportions,
        utils.YearRecord())
    self.assertEqual(withdrawn, 60)
    self.assertEqual(gains, 0)
    self.assertSequenceEqual(
        year_rec.withdrawals,
        [funds.WithdrawReceipt(80, 0, funds.FUND_TYPE_RRSP)])
    self.assertSequenceEqual(
        year_rec.deposits, [funds.DepositReceipt(16, funds.FUND_TYPE_TFSA),
                            funds.DepositReceipt(4, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 20)
    self.assertEqual(tfsa.amount, 66)
    self.assertEqual(nonreg.amount, 4)



if __name__ == '__main__':
  unittest.main()
