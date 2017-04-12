import unittest
import unittest.mock
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
    fund.GetRoom = unittest.mock.MagicMock(return_value=20)
    set_room = unittest.mock.MagicMock()
    fund.SetRoom = set_room
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_NONE),
                  year_rec.deposits)
    set_room.assert_called_with(unittest.mock.ANY, 5)

  def testDepositInsufficientRoom(self):
    fund = funds.Fund()
    fund.GetRoom = unittest.mock.MagicMock(return_value=10)
    set_room = unittest.mock.MagicMock()
    fund.SetRoom = set_room
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 10)
    self.assertEqual(fund.amount, 10)
    self.assertIn(funds.DepositReceipt(10, funds.FUND_TYPE_NONE),
                  year_rec.deposits)
    set_room.assert_called_with(unittest.mock.ANY, 0)
    
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
    fund.GetRoom = unittest.mock.MagicMock(return_value=5)
    set_room = unittest.mock.MagicMock()
    fund.SetRoom = set_room
    fund.room_replenishes = True
    withdrawn, gains, year_rec = fund.Withdraw(10, utils.YearRecord())
    set_room.assert_called_with(unittest.mock.ANY, 15)

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
  
  def testWithdrawZero(self):
    fund = funds.Fund()
    fund.amount = 0
    withdrawn, gains, year_rec = fund.Withdraw(10, utils.YearRecord())
    self.assertEqual(withdrawn, 0)
    self.assertEqual(gains, 0)
    self.assertIn(funds.WithdrawReceipt(0, 0, funds.FUND_TYPE_NONE),
                  year_rec.withdrawals)

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

  def testGrowthInflation(self):
    fund = funds.Fund()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0
    year_rec.inflation = 1
    self.assertEqual(fund.Growth(year_rec), 20)


class TFSATest(unittest.TestCase):

  @unittest.skip("Room replenishment needs to be done in person now")
  def testTFSARoom(self):
    fund = funds.TFSA()
    self.assertEqual(fund.room, world.TFSA_INITIAL_CONTRIBUTION_LIMIT)
    fund.Update(utils.YearRecord())
    self.assertEqual(fund.room, (world.TFSA_INITIAL_CONTRIBUTION_LIMIT +
                                 world.TFSA_ANNUAL_CONTRIBUTION_LIMIT))

  def testTFSADeposit(self):
    fund = funds.TFSA()
    year_rec = utils.YearRecord()
    year_rec.tfsa_room = 20
    deposited, year_rec = fund.Deposit(15, year_rec)
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_TFSA),
                  year_rec.deposits)
  
  def testTFSAWithdraw(self):
    fund = funds.TFSA()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.tfsa_room = 0
    withdrawn, gains, year_rec = fund.Withdraw(15, year_rec)
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_TFSA),
                  year_rec.withdrawals)
    self.assertEqual(year_rec.tfsa_room, 15)

  def testTFSAUpdate(self):
    fund = funds.TFSA()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.2
    year_rec.inflation = 1
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 48)
    self.assertEqual(fund.unrealized_gains, 0)


class RRSPTest(unittest.TestCase):

  @unittest.skip("Room replenishment needs to be done in person now")
  def testRRSPRoom(self):
    fund = funds.RRSP()
    year_rec = utils.YearRecord()
    year_rec.incomes.append(incomes.IncomeReceipt(10000, incomes.INCOME_TYPE_EARNINGS))
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT)
    fund.Update(year_rec)
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT+1800)

  @unittest.skip("Room replenishment needs to be done in person now")
  def testRRSPRoomLimit(self):
    fund = funds.RRSP()
    year_rec = utils.YearRecord()
    year_rec.incomes.append(incomes.IncomeReceipt(140000, incomes.INCOME_TYPE_EARNINGS))
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT)
    fund.Update(year_rec)
    self.assertEqual(fund.room, world.RRSP_INITIAL_LIMIT+world.RRSP_LIMIT)

  def testRRSPDeposit(self):
    fund = funds.RRSP()
    year_rec = utils.YearRecord()
    year_rec.rrsp_room = 20
    deposited, year_rec = fund.Deposit(15, year_rec)
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_RRSP),
                  year_rec.deposits)
    self.assertEqual(year_rec.rrsp_room, 5)
  
  def testRRSPWithdraw(self):
    fund = funds.RRSP()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.rrsp_room = 0
    withdrawn, gains, year_rec = fund.Withdraw(15, year_rec)
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_RRSP),
                  year_rec.withdrawals)
    self.assertEqual(year_rec.rrsp_room, 0)

  @unittest.skip("no more forced withdraw")
  def testRRSPForcedWithdrawEarly(self):
    fund = funds.RRSP()
    fund.amount = 10000
    year_rec = utils.YearRecord()
    year_rec.age = 69
    fund.Update(year_rec)
    self.assertEqual(fund.forced_withdraw, 0)

  @unittest.skip("no more forced withdraw")
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
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.2
    year_rec.inflation = 1
    year_rec.incomes.append(incomes.IncomeReceipt(10000, incomes.INCOME_TYPE_EARNINGS))
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 48)
    self.assertEqual(fund.unrealized_gains, 0)


class NonRegisteredTest(unittest.TestCase):

  def testNonRegisteredDeposit(self):
    fund = funds.NonRegistered()
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 15)
    self.assertEqual(fund.amount, 15)
    self.assertIn(funds.DepositReceipt(15, funds.FUND_TYPE_NONREG),
                  year_rec.deposits)
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
  
  def testNonRegisteredWithdrawNegativeUnrealizedGains(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = -10
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertEqual(fund.unrealized_gains, -2.5)
    self.assertIn(funds.WithdrawReceipt(15, -7.5, funds.FUND_TYPE_NONREG),
                  year_rec.withdrawals)
  
  def testNonRegisteredWithdrawReallyNegativeUnrealizedGains(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = -25
    withdrawn, gains, year_rec = fund.Withdraw(20, utils.YearRecord())
    self.assertEqual(withdrawn, 20)
    self.assertEqual(fund.amount, 0)
    self.assertEqual(fund.unrealized_gains, 0)
    self.assertIn(funds.WithdrawReceipt(20, -25, funds.FUND_TYPE_NONREG),
                  year_rec.withdrawals)

  def testNonRegisteredUpdateGainsIncrement(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.4
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 28)
    self.assertEqual(fund.unrealized_gains, 13.6)
    self.assertIn(funds.TaxReceipt(4.4, funds.FUND_TYPE_NONREG),
                  year_rec.tax_receipts)

  def testNonRegisteredUpdateZeroGrowth(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 20)
    self.assertAlmostEqual(fund.unrealized_gains, 8)
    self.assertAlmostEqual(year_rec.tax_receipts[0].gross_gain, 2)
    self.assertEqual(year_rec.tax_receipts[0].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(len(year_rec.tax_receipts), 1)

  def testNonRegisteredUpdateGainsDecrement(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -0.4
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 12)
    self.assertAlmostEqual(fund.unrealized_gains, 2.4)
    self.assertAlmostEqual(year_rec.tax_receipts[0].gross_gain, -0.4)
    self.assertEqual(year_rec.tax_receipts[0].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(len(year_rec.tax_receipts), 1)

  def testNonRegisteredUpdateGainsDecrementPastZero(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = 10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -0.6
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 8)
    self.assertAlmostEqual(fund.unrealized_gains, -0.4)
    self.assertAlmostEqual(year_rec.tax_receipts[0].gross_gain, -1.6)
    self.assertEqual(year_rec.tax_receipts[0].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(len(year_rec.tax_receipts), 1)

  def testNonRegisteredUpdateZeroGrowthNegativeUnrealizedGains(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = -10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 20)
    self.assertAlmostEqual(fund.unrealized_gains, -8)
    self.assertAlmostEqual(year_rec.tax_receipts[0].gross_gain, -2)
    self.assertEqual(year_rec.tax_receipts[0].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(len(year_rec.tax_receipts), 1)

  def testNonRegisteredUpdatePositiveGrowthNegativeUnrealizedGains(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = -10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.4
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 28)
    self.assertAlmostEqual(fund.unrealized_gains, -2.4)
    self.assertAlmostEqual(year_rec.tax_receipts[0].gross_gain, 0.4)
    self.assertEqual(year_rec.tax_receipts[0].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(len(year_rec.tax_receipts), 1)

  def testNonRegisteredUpdateNegativeGrowthNegativeUnrealizedGains(self):
    fund = funds.NonRegistered()
    fund.amount = 20
    fund.unrealized_gains = -10
    year_rec = utils.YearRecord()
    year_rec.growth_rate = -0.4
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 12)
    self.assertAlmostEqual(fund.unrealized_gains, -13.6)
    self.assertAlmostEqual(year_rec.tax_receipts[0].gross_gain, -4.4)
    self.assertEqual(year_rec.tax_receipts[0].fund_type, funds.FUND_TYPE_NONREG)
    self.assertEqual(len(year_rec.tax_receipts), 1)


class RRSPBridgingTest(unittest.TestCase):

  def testRRSPBridgingDeposit(self):
    fund = funds.RRSPBridging()
    fund.amount = 30
    deposited, year_rec = fund.Deposit(15, utils.YearRecord())
    self.assertEqual(deposited, 0)
    self.assertEqual(fund.amount, 30)
    self.assertIn(funds.DepositReceipt(0, funds.FUND_TYPE_BRIDGING),
                  year_rec.deposits)
  
  def testRRSPBridgingWithdraw(self):
    fund = funds.RRSPBridging()
    fund.amount = 20
    withdrawn, gains, year_rec = fund.Withdraw(15, utils.YearRecord())
    self.assertEqual(withdrawn, 15)
    self.assertEqual(fund.amount, 5)
    self.assertEqual(fund.unrealized_gains, 0)
    self.assertIn(funds.WithdrawReceipt(15, 0, funds.FUND_TYPE_BRIDGING),
                  year_rec.withdrawals)

  def testRRSPBridgingUpdate(self):
    fund = funds.RRSPBridging()
    fund.amount = 20
    year_rec = utils.YearRecord()
    year_rec.growth_rate = 0.2
    year_rec.inflation = 1
    fund.Update(year_rec)
    self.assertEqual(fund.amount, 48)
    self.assertEqual(fund.unrealized_gains, 0)


class ChainingTest(unittest.TestCase):
  
  def testChainedDeposit(self):
    year_rec = utils.YearRecord()
    tfsa = funds.TFSA()
    year_rec.tfsa_room = 30
    rrsp = funds.RRSP()
    year_rec.rrsp_room = 50
    bridging = funds.RRSPBridging()
    bridging.amount = 60
    nonreg = funds.NonRegistered()
    fund_chain = (tfsa, rrsp, bridging, nonreg)
    proportions = (1, 1, 1, 1)
    deposited, year_rec = funds.ChainedDeposit(100, fund_chain, proportions,
                                               year_rec)
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
    year_rec = utils.YearRecord()
    tfsa = funds.TFSA()
    year_rec.tfsa_room = 30
    rrsp = funds.RRSP()
    year_rec.rrsp_room = 50
    fund_chain = (tfsa, rrsp)
    proportions = (1, 1)
    deposited, year_rec = funds.ChainedDeposit(100, fund_chain, proportions,
                                               year_rec)
    self.assertEqual(deposited, 80)
    self.assertSequenceEqual(year_rec.deposits,
                             [funds.DepositReceipt(30, funds.FUND_TYPE_TFSA),
                              funds.DepositReceipt(50, funds.FUND_TYPE_RRSP)])
    self.assertEqual(tfsa.amount, 30)
    self.assertEqual(rrsp.amount, 50)
                             
  def testChainedDepositProportions(self):
    year_rec = utils.YearRecord()
    tfsa = funds.TFSA()
    year_rec.tfsa_room = 30
    rrsp = funds.RRSP()
    year_rec.rrsp_room = 30
    nonreg = funds.NonRegistered()
    fund_chain = (tfsa, rrsp, nonreg)
    proportions = (0.2, 0.5, 1)
    deposited, year_rec = funds.ChainedDeposit(100, fund_chain, proportions,
                                               year_rec)
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
    self.assertAlmostEqual(withdrawn, 60)
    self.assertAlmostEqual(gains, 13.5)
    self.assertAlmostEqual(rrsp.amount, 14)
    self.assertAlmostEqual(tfsa.amount, 23)
    self.assertAlmostEqual(nonreg.amount, 3)
    self.assertAlmostEqual(nonreg.unrealized_gains, 1.5)

  def testChainedWithdrawInsufficientFunds(self):
    rrsp = funds.RRSP()
    rrsp.amount = 20
    tfsa = funds.TFSA()
    tfsa.amount = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 20
    nonreg.unrealized_gains = 10
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(160, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertAlmostEqual(withdrawn, 90)
    self.assertAlmostEqual(gains, 10)
    self.assertAlmostEqual(rrsp.amount, 0)
    self.assertAlmostEqual(tfsa.amount, 0)
    self.assertAlmostEqual(nonreg.amount, 0)

  def testChainedWithdrawPartialInsufficientFunds(self):
    rrsp = funds.RRSP()
    rrsp.amount = 30
    tfsa = funds.TFSA()
    tfsa.amount = 16
    nonreg = funds.NonRegistered()
    nonreg.amount = 40
    nonreg.unrealized_gains = 20
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (1/3, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertAlmostEqual(withdrawn, 60)
    self.assertAlmostEqual(gains, 11)
    self.assertAlmostEqual(rrsp.amount, 8)
    self.assertAlmostEqual(tfsa.amount, 0)
    self.assertAlmostEqual(nonreg.amount, 18)

  @unittest.skip("no more forced withdraw")
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

  @unittest.skip("no more forced withdraw")
  def testChainedWithdrawForcedWithdrawPreferZero(self):
    year_rec = utils.YearRecord()
    year_rec.age = 94
    year_rec.growth_rate=0
    rrsp = funds.RRSP()
    rrsp.amount = 50
    rrsp.Update(year_rec)
    tfsa = funds.TFSA()
    tfsa.amount = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 30
    nonreg.unrealized_gains = 15
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0, 0.5, 1)
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
    self.assertEqual(rrsp.amount, 40)
    self.assertEqual(tfsa.amount, 25)
    self.assertEqual(nonreg.amount, 5)

  @unittest.skip("no more forced withdraw")
  def testChainedWithdrawForcedWithdrawProportionalDeposit(self):
    year_rec = utils.YearRecord()
    rrsp = funds.RRSP()
    rrsp.amount = 100
    rrsp.forced_withdraw = 80
    tfsa = funds.TFSA()
    tfsa.amount = 50
    year_rec.tfsa_room = 50
    nonreg = funds.NonRegistered()
    nonreg.amount = 50
    nonreg.unrealized_gains = 25
    fund_chain = (rrsp, tfsa, nonreg)
    proportions = (0.1, 0.5, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(60, fund_chain,
                                                       proportions,
                                                       year_rec)
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

  @unittest.skip("no more forced withdraw")
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

  @unittest.skip("no more forced withdraw")
  def testChainedWithdrawForcedWithdrawWantZero(self):
    rrsp = funds.RRSP()
    rrsp.amount = 100
    rrsp.forced_withdraw = 20
    nonreg = funds.NonRegistered()
    fund_chain = (rrsp, nonreg)
    proportions = (0, 1)
    withdrawn, gains, year_rec = funds.ChainedWithdraw(0, fund_chain,
                                                       proportions,
                                                       utils.YearRecord())
    self.assertEqual(withdrawn, 0)
    self.assertEqual(gains, 0)
    self.assertSequenceEqual(
        year_rec.withdrawals,
        [funds.WithdrawReceipt(20, 0, funds.FUND_TYPE_RRSP)])
    self.assertSequenceEqual(
        year_rec.deposits, [funds.DepositReceipt(20, funds.FUND_TYPE_NONREG)])
    self.assertEqual(rrsp.amount, 80)
    self.assertEqual(nonreg.amount, 20)

  def testChainedTransactionDifferentProportion(self):
    year_rec = utils.YearRecord()
    rrsp = funds.RRSP()
    rrsp.amount = 100
    rrsp.forced_withdraw = 80
    tfsa = funds.TFSA()
    tfsa.amount = 50
    year_rec.tfsa_room = 100
    nonreg = funds.NonRegistered()
    fund_chain = (rrsp, tfsa, nonreg)
    withdrawal_proportions = (0.5, 0.5, 1)
    deposit_proportions = (0.5, 0.8, 1)
    withdrawn, gains, year_rec = funds.ChainedTransaction(
        60, fund_chain, withdrawal_proportions, deposit_proportions,
        year_rec)
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


class TestSplitFund(unittest.TestCase):

  def testSplitFundSufficientFunds(self):
    source = funds.Fund()
    source.amount = 40
    source.unrealized_gains = 20
    sink = funds.Fund()
    source, sink = funds.SplitFund(source, sink, 30)
    self.assertEqual(source.amount, 10)
    self.assertEqual(sink.amount, 30)
    self.assertEqual(source.unrealized_gains, 5)
    self.assertEqual(sink.unrealized_gains, 15)

  def testSplitFundInsufficientFunds(self):
    source = funds.Fund()
    source.amount = 40
    source.unrealized_gains = 20
    sink = funds.Fund()
    source, sink = funds.SplitFund(source, sink, 50)
    self.assertEqual(source.amount, 0)
    self.assertEqual(sink.amount, 40)
    self.assertEqual(source.unrealized_gains, 0)
    self.assertEqual(sink.unrealized_gains, 20)

  def testSplitFundSinkHasMoney(self):
    source = funds.Fund()
    source.amount = 40
    source.unrealized_gains = 20
    sink = funds.Fund()
    sink.amount = 20
    sink.unrealized_gains = 10
    source, sink = funds.SplitFund(source, sink, 30)
    self.assertEqual(source.amount, 10)
    self.assertEqual(sink.amount, 50)
    self.assertEqual(source.unrealized_gains, 5)
    self.assertEqual(sink.unrealized_gains, 25)

  def testSplitFundSourceHasZeroFunds(self):
    source = funds.Fund()
    source.amount = 0
    source.unrealized_gains = 0
    sink = funds.Fund()
    source, sink = funds.SplitFund(source, sink, 30)
    self.assertEqual(source.amount, 0)
    self.assertEqual(sink.amount, 0)
    self.assertEqual(source.unrealized_gains, 0)
    self.assertEqual(sink.unrealized_gains, 0)


if __name__ == '__main__':
  unittest.main()
