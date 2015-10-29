import collections
import random
import incomes
import funds
import utils
import world

MALE = "m"
FEMALE = "f"

Strategy = collections.namedtuple("Strategy",
                                  ["planned_retirement_age",
                                   "savings_threshold",
                                   "savings_rate",
                                   "savings_rrsp_fraction",
                                   "savings_tfsa_fraction",
                                   "lico_target_fraction",
                                   "working_period_drawdown_tfsa_fraction",
                                   "working_period_drawdown_nonreg_fraction",
                                   "oas_bridging_fraction",
                                   "drawdown_ced_fraction",
                                   "initial_cd_fraction",
                                   "drawdown_preferred_rrsp_fraction",
                                   "drawdown_preferred_tfsa_fraction",
                                   "reinvestment_preference_tfsa_fraction",])

class Person(object):
  
  def __init__(self, strategy, gender=FEMALE):
    self.year = world.BASE_YEAR
    self.age = world.START_AGE
    self.gender = gender
    self.strategy = strategy
    self.employed_last_year = True
    self.retired = False
    self.incomes = [incomes.Earnings(), incomes.EI(), incomes.CPP(), incomes.OAS(), incomes.GIS()]
    self.funds = {"wp_tfsa": funds.TFSA(), "wp_rrsp": funds.RRSP(), "wp_nonreg": funds.NonRegistered()}
    self.involuntary_retirement_random = random.random()
    self.tfsa_room = world.TFSA_INITIAL_CONTRIBUTION_LIMIT
    self.rrsp_room = world.RRSP_INITIAL_LIMIT
    self.capital_loss_carry_forward = 0


  def OnRetirement(self):
    """This deals with events happening at the point of retirement."""

    # Update all incomes
    for income in self.incomes:
      income.OnRetirement(self)

    # Create RRSP bridging fund if needed
    if self.age < world.CPP_EXPECTED_RETIREMENT_AGE:
      requested = (world.CPP_EXPECTED_RETIREMENT_AGE - self.age) * world.OAS_BENEFIT
      self.funds["wp_rrsp"], self.funds["bridging"] = funds.SplitFund(self.funds["wp_rrsp"], funds.RRSPBridging(), requested)
      self.bridging_annual_withdrawal = self.funds["bridging"].amount / (world.CPP_EXPECTED_RETIREMENT_AGE - self.age)

    # Split each fund into a CED and a CD fund
    self.funds["cd_rrsp"], self.funds["ced_rrsp"] = funds.SplitFund(self.funds["wp_rrsp"], funds.RRSP(), self.strategy.drawdown_ced_fraction * self.funds["wp_rrsp"].amount)
    del self.funds["wp_rrsp"]
    
    self.funds["cd_tfsa"], self.funds["ced_tfsa"] = funds.SplitFund(self.funds["wp_tfsa"], funds.TFSA(), self.strategy.drawdown_ced_fraction * self.funds["wp_tfsa"].amount)
    del self.funds["wp_tfsa"]
    
    self.funds["cd_nonreg"], self.funds["ced_nonreg"] = funds.SplitFund(self.funds["wp_nonreg"], funds.NonRegistered(), self.strategy.drawdown_ced_fraction * self.funds["wp_nonreg"].amount)
    del self.funds["wp_nonreg"]

    self.cd_drawdown_amount = sum(fund.amount for fund in (self.funds["cd_rrsp"], self.funds["cd_tfsa"], self.funds["cd_nonreg"])) * self.strategy.initial_cd_fraction


  def AnnualSetup(self):
    """This is responsible for beginning of year operations.

    Returns a partially initialized year record.
    """
    year_rec = utils.YearRecord()
    year_rec.age = self.age
    year_rec.year = self.year

    # Reap souls
    if self.gender == MALE:
      p_mortality = world.MALE_MORTALITY[self.age] * world.MORTALITY_MULTIPLIER
    elif self.gender == FEMALE:
      p_mortality = world.FEMALE_MORTALITY[self.age] * world.MORTALITY_MULTIPLIER

    if random.random() < p_mortality:
      year_rec.is_dead = True
      return year_rec
    else:
      year_rec.is_dead = False

    # Retirement
    if not self.retired:
      if ((self.age == self.strategy.planned_retirement_age and self.age >= world.MINIMUM_RETIREMENT_AGE) or
          self.involuntary_retirement_random < (self.age - world.MINIMUM_RETIREMENT_AGE + 1) * world.INVOLUNTARY_RETIREMENT_INCREMENT):
        self.retired = True
        self.OnRetirement()
    year_rec.is_retired = self.retired

    # Employment
    year_rec.is_employed = not self.retired and random.random() > world.UNEMPLOYMENT_PROBABILITY

    # Growth
    year_rec.growth_rate = random.normalvariate(world.MEAN_INVESTMENT_RETURN, world.STD_INVESTMENT_RETURN)

    # Fund room
    year_rec.tfsa_room = self.tfsa_room
    year_rec.rrsp_room = self.rrsp_room

    return year_rec

  def CalcIncomeTax(self, year_rec):
    """Calculates the amount of income tax to be paid"""
    # Calculate Total Income
    income_sum = sum(receipt.amount for receipt in year_rec.incomes)
    rrsp_withdrawal_sum = sum(receipt.amount for receipt in year_rec.withdrawals
                              if receipt.fund_type in (funds.FUND_TYPE_RRSP, funds.FUND_TYPE_BRIDGING))
    capital_gains = (sum(receipt.gains for receipt in year_rec.withdrawals) +
                     sum(receipt.gross_gain for receipt in year_rec.tax_receipts))
    if capital_gains > 0:
      taxable_capital_gains = capital_gains * world.CG_INCLUSION_RATE
    else:
      self.capital_loss_carry_forward += -capital_gains
      taxable_capital_gains = 0

    cpp_death_benefit = world.CPP_DEATH_BENEFIT if year_rec.is_dead else 0

    total_income = income_sum + rrsp_withdrawal_sum + taxable_capital_gains + cpp_death_benefit

    # Calculate Net Income before adjustments
    rrsp_contribution_sum = sum(receipt.amount for receipt in year_rec.deposits
                                  if receipt.fund_type == funds.FUND_TYPE_RRSP)
    net_income_before_adjustments = max(total_income - rrsp_contribution_sum, 0)

    # Employment Insurance Social Benefits Repayment
    ei_benefits = sum(receipt.amount for receipt in year_rec.incomes
                     if receipt.income_type == incomes.INCOME_TYPE_EI)
    ei_base_amount = utils.Indexed(world.EI_MAX_INSURABLE_EARNINGS, year_rec.year, 1 + world.PARGE) * world.EI_REPAYMENT_BASE_FRACTION
    ei_benefit_repayment = min(max(0, net_income_before_adjustments - ei_base_amount), ei_benefits) * world.EI_REPAYMENT_REDUCTION_RATE

    # Old Age Security and Net Federal Supplements Repayment
    oas_plus_gis = sum(receipt.amount for receipt in year_rec.incomes
                     if receipt.income_type in (incomes.INCOME_TYPE_OAS, incomes.INCOME_TYPE_GIS))

    income_over_base_amount = max(0, max(0, net_income_before_adjustments-ei_benefit_repayment)-world.OAS_CLAWBACK_EXEMPTION) * world.OAS_CLAWBACK_RATE
    oas_and_gis_repayment = min(oas_plus_gis, income_over_base_amount)

    # Total Social Benefit Repayment
    total_social_benefit_repayment = ei_benefit_repayment + oas_and_gis_repayment

    # Other Payments Deduction
    gis_income = sum(receipt.amount for receipt in year_rec.incomes
                     if receipt.income_type == incomes.INCOME_TYPE_GIS)
    oas_income = sum(receipt.amount for receipt in year_rec.incomes
                     if receipt.income_type == incomes.INCOME_TYPE_OAS)
    try:
      oas_benefit_repaid = oas_and_gis_repayment * oas_income / (gis_income + oas_income)
    except ZeroDivisionError:
      oas_benefit_repaid = 0
    net_federal_supplements_deduction = gis_income - (total_social_benefit_repayment - (ei_benefit_repayment + oas_benefit_repaid))

    # Net Income
    net_income = net_income_before_adjustments - total_social_benefit_repayment

    # Taxable Income
    applied_capital_loss_amount = min(taxable_capital_gains, self.capital_loss_carry_forward * world.CG_INCLUSION_RATE)
    taxable_income = max(0, net_income - (net_federal_supplements_deduction + applied_capital_loss_amount))

    # Age amount
    age_amount_reduction = max(0, net_income - world.AGE_AMOUNT_EXEMPTION) * world.AGE_AMOUNT_REDUCTION_RATE
    age_amount = max(0, world.AGE_AMOUNT_MAXIMUM - age_amount_reduction)

    # CPP employee contribution
    earnings = sum(receipt.amount for receipt in year_rec.incomes
                   if receipt.income_type == incomes.INCOME_TYPE_EARNINGS)
    year_rec.pensionable_earnings = max(0, min(utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE), earnings) - world.YBE)
    cpp_employee_contribution = year_rec.pensionable_earnings * world.CPP_EMPLOYEE_RATE

    # EI premium
    year_rec.insurable_earnings = min(earnings, utils.Indexed(world.EI_MAX_INSURABLE_EARNINGS, year_rec.year, 1 + world.PARGE))
    ei_premium = year_rec.insurable_earnings * world.EI_PREMIUM_RATE

    # Federal non-refundable tax credits
    federal_non_refundable_credits = (world.BASIC_PERSONAL_AMOUNT + age_amount + cpp_employee_contribution + ei_premium) * world.NON_REFUNDABLE_CREDIT_RATE 

    # Federal tax on taxable income
    net_federal_tax = max(0, world.FEDERAL_TAX_SCHEDULE[taxable_income] - federal_non_refundable_credits)

    # Tax payable
    tax_payable = net_federal_tax + total_social_benefit_repayment + net_federal_tax * world.PROVINCIAL_TAX_FRACTION

    return tax_payable

  def MeddleWithCash(self, year_rec):
    """This performs all operations on subject's cash pile"""
    cash = 0

    # Get money from incomes
    for income in self.incomes:
      amount, taxable, year_rec = income.GiveMeMoney(year_rec)
      cash += amount

    # Do withdrawals
    if self.is_retired:
      # Bridging 
      if "bridging" in self.funds and self.age < world.CPP_EXPECTED_RETIREMENT_AGE:
        withdrawn, gains, year_rec = self.funds["bridging"].Withdraw(self.bridging_annual_withdrawal, year_rec)
        cash += withdrawn

      # CD drawdown strategy
      proportions = (self.strategy.drawdown_preferred_rrsp_fraction, self.strategy.drawdown_preferred_tfsa_fraction, 1)
      fund_chain = [self.funds["cd_rrsp"], self.funds["cd_tfsa"], self.funds["cd_nonreg"]]
      withdrawn, gains, year_rec = funds.ChainedWithdraw(self.cd_drawdown_amount, fund_chain, proportions, year_rec)
      cash += withdrawn

      # CED drawdown_strategy
      fund_chain = [self.funds["ced_rrsp"], self.funds["ced_tfsa"], self.funds["ced_nonreg"]]
      ced_drawdown_amount = sum(f.amount for f in fund_chain) * world.CED_PROPORTION[self.age]
      withdrawn, gains, year_rec = funds.ChainedWithdraw(ced_drawdown_amount, fund_chain, proportions, year_rec)
      cash += withdrawn
    else:
      if cash < world.LICO_SINGLE_CITY_WP * self.strategy.lico_target_fraction:
        # Attempt to withdraw difference from savings
        amount_to_withdraw = world.LICO_SINGLE_CITY_WP * self.strategy.lico_target_fraction - cash
        proportions = (self.strategy.working_period_drawdown_tfsa_fraction, self.strategy.working_period_drawdown_nonreg_fraction, 1)
        fund_chain = [self.funds["wp_tfsa"], self.funds["wp_nonreg"], self.funds["wp_rrsp"]]
        withdrawn, gains, year_rec = funds.ChainedWithdraw(amount_to_withdraw, fund_chain, proportions, year_rec)
        cash += withdrawn

    # Save
    if not self.is_retired:
      earnings_to_save = max(earnings-self.strategy.savings_threshold, 0) * self.strategy.savings_rate
      proportions = (self.strategy.savings_rrsp_fraction, self.strategy.savings_tfsa_fraction, 1)
      fund_chain = [self.funds["wp_rrsp"], self.funds["wp_tfsa"], self.funds["wp_nonreg"]]
      deposited, year_rec = funds.ChainedDeposit(earnings_to_save, fund_chain, proportions, year_rec)
      cash -= deposited

    # Update funds
    for fund in self.funds.values():
      fund.Update(year_rec)

    # Pay income taxes
    cash -= self.CalcIncomeTax(year_rec)
    
    # Update incomes
    for income in self.incomes:
      income.AnnualUpdate(year_rec)

    # Pay sales tax
    non_hst_consumption = min(cash, world.SALES_TAX_EXEMPTION)
    hst_consumption = cash - non_hst_consumption
    year_rec.consumption = hst_consumption / (1 + world.HST_RATE) + non_hst_consumption


  def AnnualReview(self, year_rec):
    """End of year calculations for a live person"""
    self.age += 1
    self.year += 1


  def EndOfLifeCalcs(self):
    """Calculations that happen upon death"""

  def DoYear(self):
    """Execute one year of life"""
    year_rec = self.AnnualSetup()
    if not year_rec.is_dead:
      year_rec = self.MeddleWithCash(year_rec)
      self.AnnualReview(year_rec)
    else:
      self.EndOfLifeCalcs()

  def LiveLife(self):
    """Run through one lifetime"""

