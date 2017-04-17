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
                                   "working_period_drawdown_tfsa_fraction",
                                   "working_period_drawdown_nonreg_fraction",
                                   "oas_bridging_fraction",
                                   "drawdown_ced_fraction",
                                   "initial_cd_fraction",
                                   "drawdown_preferred_rrsp_fraction",
                                   "drawdown_preferred_tfsa_fraction",
                                  ])

EMPLOYED = 0
UNEMPLOYED = 1
RETIRED = 2
INVOLUNTARILY_RETIRED = 3

class Person(object):
  
  def __init__(self, strategy, gender=FEMALE, basic_only=False, real_values=True):
    self.year = world.BASE_YEAR
    self.age = world.START_AGE
    self.gender = gender
    self.strategy = strategy
    self.cpi = 1  # Ignoring factor of 100 and StatsCan rounding rules here.
    self.cpi_history = []
    self.basic_only=basic_only
    self.real_values=real_values
    self.employed_last_year = True
    self.retired = False
    # CAUTION: GIS must be the last income in the list.
    self.incomes = [incomes.Earnings(), incomes.EI(), incomes.CPP(), incomes.OAS(), incomes.GIS()]
    self.funds = {"wp_tfsa": funds.TFSA(), "wp_rrsp": funds.RRSP(), "wp_nonreg": funds.NonRegistered()}
    self.involuntary_retirement_random = random.random()
    self.tfsa_room = world.TFSA_INITIAL_CONTRIBUTION_LIMIT
    self.rrsp_room = world.RRSP_INITIAL_LIMIT
    self.capital_loss_carry_forward = 0

    self.accumulators = utils.AccumulatorBundle()
    self.has_been_ruined = False
    self.has_received_gis = False
    self.has_experienced_income_under_lico = False

    # The following hold real dollar amounts
    self.assets_at_retirement = 0
    self.total_retirement_withdrawals = 0
    self.total_lifetime_withdrawals = 0
    self.total_working_savings = 0

    self.positive_earnings_years = 0
    self.positive_savings_years = 0
    self.ei_years = 0
    self.gis_years = 0
    self.gross_income_below_lico_years = 0
    self.no_assets_years = 0

    self.period_years = {EMPLOYED: 0, UNEMPLOYED: 0, RETIRED: 0, INVOLUNTARILY_RETIRED: 0}

  def OnRetirement(self, year_rec):
    """This deals with events happening at the point of retirement."""

    # Update all incomes
    for income in self.incomes:
      income.OnRetirement(self)

    # Create RRSP bridging fund if needed
    if self.age < world.CPP_EXPECTED_RETIREMENT_AGE:
      requested = (world.CPP_EXPECTED_RETIREMENT_AGE - self.age) * world.OAS_BENEFIT * self.strategy.oas_bridging_fraction
      self.funds["wp_rrsp"], self.funds["bridging"] = funds.SplitFund(self.funds["wp_rrsp"], funds.RRSPBridging(), requested)
      if self.funds["bridging"].amount < requested:
        top_up_amount = min(self.rrsp_room, requested - self.funds["bridging"].amount)
        fund_chain = [self.funds["wp_nonreg"], self.funds["wp_tfsa"]]
        # Not using ChainedWithdraw because it can't express strict overflow
        withdrawn, _, year_rec = funds.ChainedTransaction(top_up_amount, fund_chain, (1, 1), (1, 1), year_rec)
        self.funds["bridging"].amount += withdrawn
        year_rec.deposits.append(funds.DepositReceipt(withdrawn, funds.FUND_TYPE_RRSP))
        self.rrsp_room -= withdrawn

      self.bridging_withdrawal_table = world.GenerateCEDDrawdownTable(self.age, world.CPP_EXPECTED_RETIREMENT_AGE)

    # Split each fund into a CED and a CD fund
    self.funds["cd_rrsp"], self.funds["ced_rrsp"] = funds.SplitFund(self.funds["wp_rrsp"], funds.RRSP(), self.strategy.drawdown_ced_fraction * self.funds["wp_rrsp"].amount)
    del self.funds["wp_rrsp"]
    
    self.funds["cd_tfsa"], self.funds["ced_tfsa"] = funds.SplitFund(self.funds["wp_tfsa"], funds.TFSA(), self.strategy.drawdown_ced_fraction * self.funds["wp_tfsa"].amount)
    del self.funds["wp_tfsa"]
    
    self.funds["cd_nonreg"], self.funds["ced_nonreg"] = funds.SplitFund(self.funds["wp_nonreg"], funds.NonRegistered(), self.strategy.drawdown_ced_fraction * self.funds["wp_nonreg"].amount)
    del self.funds["wp_nonreg"]

    self.cd_drawdown_amount = sum(fund.amount for fund in (self.funds["cd_rrsp"], self.funds["cd_tfsa"], self.funds["cd_nonreg"])) * self.strategy.initial_cd_fraction / year_rec.cpi

    self.assets_at_retirement = sum(fund.amount for fund in self.funds.values()) / year_rec.cpi

    if not self.basic_only:
      self.accumulators.fraction_persons_involuntarily_retired.UpdateOneValue(1 if self.age < self.strategy.planned_retirement_age else 0)


  def AnnualSetup(self):
    """This is responsible for beginning of year operations.

    Returns a partially initialized year record.
    """
    year_rec = utils.YearRecord()
    year_rec.age = self.age
    year_rec.year = self.year
    year_rec.inflation = random.normalvariate(world.INFLATION_MEAN, world.INFLATION_STDDEV)
    if self.year == world.BASE_YEAR:
      self.cpi = 1
    else:
      self.cpi = self.cpi * (1 + year_rec.inflation)
    self.cpi_history.append(self.cpi)
    year_rec.cpi = self.cpi


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
          self.involuntary_retirement_random < (self.age - world.MINIMUM_RETIREMENT_AGE + 1) * world.INVOLUNTARY_RETIREMENT_INCREMENT or
          self.age == world.MAXIMUM_RETIREMENT_AGE):
        self.retired = True
        self.OnRetirement(year_rec)
    year_rec.is_retired = self.retired

    # Employment
    year_rec.is_employed = not self.retired and random.random() > world.UNEMPLOYMENT_PROBABILITY

    # Growth
    year_rec.growth_rate = random.normalvariate(world.MEAN_INVESTMENT_RETURN, world.STD_INVESTMENT_RETURN)

    # Fund room
    self.tfsa_room += world.TFSA_ANNUAL_CONTRIBUTION_LIMIT * self.cpi
    year_rec.tfsa_room = self.tfsa_room
    year_rec.rrsp_room = self.rrsp_room

    return year_rec

  def CalcPayrollDeductions(self, year_rec):
    """Calculates and stores EI premium and CPP employee controbutions"""
    # CPP employee contribution
    earnings = sum(receipt.amount for receipt in year_rec.incomes
                   if receipt.income_type == incomes.INCOME_TYPE_EARNINGS)
    year_rec.pensionable_earnings = max(0, min(utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE) * year_rec.cpi, earnings) - world.YBE)
    year_rec.cpp_contribution = year_rec.pensionable_earnings * world.CPP_EMPLOYEE_RATE

    # EI premium
    year_rec.insurable_earnings = min(earnings, utils.Indexed(world.EI_MAX_INSURABLE_EARNINGS, year_rec.year, 1 + world.PARGE) * year_rec.cpi)
    year_rec.ei_premium = year_rec.insurable_earnings * world.EI_PREMIUM_RATE

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
    year_rec.taxable_capital_gains = taxable_capital_gains

    cpp_death_benefit = world.CPP_DEATH_BENEFIT if year_rec.is_dead else 0

    total_income = income_sum + rrsp_withdrawal_sum + taxable_capital_gains + cpp_death_benefit

    # Calculate Net Income before adjustments
    rrsp_contribution_sum = sum(receipt.amount for receipt in year_rec.deposits
                                  if receipt.fund_type == funds.FUND_TYPE_RRSP)
    net_income_before_adjustments = max(total_income - rrsp_contribution_sum, 0)

    # Employment Insurance Social Benefits Repayment
    ei_benefits = sum(receipt.amount for receipt in year_rec.incomes
                     if receipt.income_type == incomes.INCOME_TYPE_EI)
    ei_base_amount = utils.Indexed(world.EI_MAX_INSURABLE_EARNINGS, year_rec.year, 1 + world.PARGE) * world.EI_REPAYMENT_BASE_FRACTION * year_rec.cpi
    ei_benefit_repayment = min(max(0, net_income_before_adjustments - ei_base_amount), ei_benefits) * world.EI_REPAYMENT_REDUCTION_RATE

    # Old Age Security and Net Federal Supplements Repayment
    oas_plus_gis = sum(receipt.amount for receipt in year_rec.incomes
                     if receipt.income_type in (incomes.INCOME_TYPE_OAS, incomes.INCOME_TYPE_GIS))

    prospective_social_benefit_repayment = max(0, max(0, net_income_before_adjustments-ei_benefit_repayment)-world.SBR_BASE_AMOUNT*year_rec.cpi) * world.SBR_REDUCTION_RATE
    oas_and_gis_repayment = min(oas_plus_gis, prospective_social_benefit_repayment)

    # Total Social Benefit Repayment
    total_social_benefit_repayment = ei_benefit_repayment + oas_and_gis_repayment
    year_rec.total_social_benefit_repayment = total_social_benefit_repayment

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
    year_rec.taxable_income = taxable_income

    # Age amount
    age_amount_reduction = max(0, net_income - world.AGE_AMOUNT_EXEMPTION * year_rec.cpi) * world.AGE_AMOUNT_REDUCTION_RATE
    age_amount = max(0, world.AGE_AMOUNT_MAXIMUM * year_rec.cpi - age_amount_reduction)

    # Federal non-refundable tax credits
    if year_rec.is_dead:
      federal_non_refundable_credits = 0
    else:
      federal_non_refundable_credits = (world.BASIC_PERSONAL_AMOUNT * year_rec.cpi + age_amount + year_rec.cpp_contribution + year_rec.ei_premium) * world.NON_REFUNDABLE_CREDIT_RATE 

    # Federal tax on taxable income
    # Tax schedule is in real terms, so we need to convert to/from nominal values
    net_federal_tax = max(0, world.FEDERAL_TAX_SCHEDULE[taxable_income / year_rec.cpi] * year_rec.cpi - federal_non_refundable_credits)

    # Tax payable
    tax_payable = net_federal_tax + total_social_benefit_repayment + net_federal_tax * world.PROVINCIAL_TAX_FRACTION

    return tax_payable

  def CalcEndOfLifeEstate(self, year_rec):
    # Withdraw all money from all funds to generate the relevant receipts
    total_funds_amount = 0
    for fund in self.funds.values():
      withdrawn, gains, year_rec = fund.Withdraw(fund.amount, year_rec)
      total_funds_amount += withdrawn

    # Gross estate at death
    gross_estate = total_funds_amount + world.CPP_DEATH_BENEFIT
    year_rec.gross_estate = gross_estate

    # Probate tax
    probate_below = world.PROBATE_RATE_BELOW * min(gross_estate, world.PROBATE_RATE_CHANGE_LEVEL)
    probate_above = world.PROBATE_RATE_ABOVE * max(0, gross_estate - world.PROBATE_RATE_CHANGE_LEVEL)
    
    # Final income tax return
    income_taxes_payable = self.CalcIncomeTax(year_rec)

    net_estate_after_tax = max(0, gross_estate - (probate_below + probate_above + income_taxes_payable))
    year_rec.estate_taxes = (probate_below + probate_above + income_taxes_payable)
    
    # Funeral and executor costs
    year_rec.funeral_and_executor_fee = world.EXECUTOR_COST_FRACTION * gross_estate + world.FUNERAL_COST

    # Final estate value
    estate = max(0, net_estate_after_tax - year_rec.funeral_and_executor_fee)
    return estate

  def MeddleWithCash(self, year_rec):
    """This performs all operations on subject's cash pile"""
    cash = 0

    # Get money from incomes. GIS is excluded and done after withdrawals
    for income in self.incomes[:-1]:
      amount, taxable, year_rec = income.GiveMeMoney(year_rec)
      cash += amount

    # Update RRSP room
    earnings = sum(receipt.amount for receipt in year_rec.incomes
                   if receipt.income_type == incomes.INCOME_TYPE_EARNINGS)
    self.rrsp_room += min(earnings * world.RRSP_ACCRUAL_FRACTION,
                          utils.Indexed(world.RRSP_LIMIT, year_rec.year, 1 + world.PARGE) * year_rec.cpi)
    year_rec.rrsp_room = self.rrsp_room

    # Do withdrawals
    if self.retired:
      # Bridging 
      if "bridging" in self.funds and self.age < world.CPP_EXPECTED_RETIREMENT_AGE:
        bridging_withdrawal_amount = self.bridging_withdrawal_table[self.age] * self.funds["bridging"].amount
        withdrawn, gains, year_rec = self.funds["bridging"].Withdraw(bridging_withdrawal_amount, year_rec)
        cash += withdrawn
        self.total_retirement_withdrawals += withdrawn / year_rec.cpi
        self.total_lifetime_withdrawals += withdrawn / year_rec.cpi

      # CD drawdown strategy
      proportions = (self.strategy.drawdown_preferred_rrsp_fraction, self.strategy.drawdown_preferred_tfsa_fraction, 1)
      fund_chain = [self.funds["cd_rrsp"], self.funds["cd_tfsa"], self.funds["cd_nonreg"]]
      cd_drawdown_amount = self.cd_drawdown_amount * year_rec.cpi
      withdrawn, gains, year_rec = funds.ChainedWithdraw(cd_drawdown_amount, fund_chain, proportions, year_rec)
      cash += withdrawn
      year_rec.cd_drawdown_amount = withdrawn
      self.total_retirement_withdrawals += withdrawn / year_rec.cpi
      self.total_lifetime_withdrawals += withdrawn / year_rec.cpi

      # CED drawdown_strategy
      fund_chain = [self.funds["ced_rrsp"], self.funds["ced_tfsa"], self.funds["ced_nonreg"]]
      ced_drawdown_amount = sum(f.amount for f in fund_chain) * world.CED_PROPORTION[self.age]
      withdrawn, gains, year_rec = funds.ChainedWithdraw(ced_drawdown_amount, fund_chain, proportions, year_rec)
      cash += withdrawn
      year_rec.ced_drawdown_amount = withdrawn
      self.total_retirement_withdrawals += withdrawn / year_rec.cpi
      self.total_lifetime_withdrawals += withdrawn / year_rec.cpi
    else:
      target_cash = utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE) * year_rec.cpi * self.strategy.savings_threshold * world.EARNINGS_YMPE_FRACTION
      if cash < target_cash:
        # Attempt to withdraw difference from savings
        amount_to_withdraw = target_cash - cash
        proportions = (self.strategy.working_period_drawdown_tfsa_fraction, self.strategy.working_period_drawdown_nonreg_fraction, 1)
        fund_chain = [self.funds["wp_tfsa"], self.funds["wp_nonreg"], self.funds["wp_rrsp"]]
        withdrawn, gains, year_rec = funds.ChainedWithdraw(amount_to_withdraw, fund_chain, proportions, year_rec)
        cash += withdrawn
        self.total_lifetime_withdrawals += withdrawn / year_rec.cpi
      else:
        # Save
        earnings_to_save = max(earnings - target_cash, 0) * self.strategy.savings_rate
        proportions = (self.strategy.savings_rrsp_fraction, self.strategy.savings_tfsa_fraction, 1)
        fund_chain = [self.funds["wp_rrsp"], self.funds["wp_tfsa"], self.funds["wp_nonreg"]]
        deposited, year_rec = funds.ChainedDeposit(earnings_to_save, fund_chain, proportions, year_rec)
        cash -= deposited
        self.total_working_savings += deposited / year_rec.cpi
        if deposited > 0:
          self.positive_savings_years += 1

    # Update funds
    for fund in self.funds.values():
      fund.Update(year_rec)

    # update the Person's view of RRSP and TFSA room
    self.tfsa_room = year_rec.tfsa_room
    self.rrsp_room = year_rec.rrsp_room

    # Calculate EI premium and CPP contributions
    year_rec = self.CalcPayrollDeductions(year_rec)

    # Now we try to get money from GIS because year_rec is populated with the needed values.
    income = self.incomes[-1]  # GIS is last in this list
    amount, taxable, year_rec = income.GiveMeMoney(year_rec)
    cash += amount

    # Pay income taxes
    year_rec.taxes_payable = self.CalcIncomeTax(year_rec)
    cash -= year_rec.taxes_payable
    
    # Update incomes
    for income in self.incomes:
      income.AnnualUpdate(year_rec)

    # Pay sales tax
    non_hst_consumption = min(cash, world.SALES_TAX_EXEMPTION)
    hst_consumption = cash - non_hst_consumption
    year_rec.consumption = hst_consumption / (1 + world.HST_RATE) + non_hst_consumption
    year_rec.sales_taxes = hst_consumption * world.HST_RATE 

    return year_rec


  def Period(self, year_rec):
    if self.retired and self.age < self.strategy.planned_retirement_age:
      return INVOLUNTARILY_RETIRED
    elif self.retired:
      return RETIRED
    elif year_rec.is_dead or year_rec.is_employed:
      return EMPLOYED
    else:
      return UNEMPLOYED


  def AnnualReview(self, year_rec):
    """End of year calculations for a live person"""
    period = self.Period(year_rec)
    self.period_years[period] += 1
    cpi = year_rec.cpi if self.real_values else 1

    self.accumulators.UpdateConsumption(year_rec.consumption/cpi, self.year, self.retired, period)
    earnings = sum(receipt.amount for receipt in year_rec.incomes
                   if receipt.income_type == incomes.INCOME_TYPE_EARNINGS)
    cpp = sum(receipt.amount for receipt in year_rec.incomes
              if receipt.income_type == incomes.INCOME_TYPE_CPP)
    ei_benefits =  sum(receipt.amount for receipt in year_rec.incomes
                       if receipt.income_type == incomes.INCOME_TYPE_EI)
    gis = sum(receipt.amount for receipt in year_rec.incomes
              if receipt.income_type == incomes.INCOME_TYPE_GIS)
    oas = sum(receipt.amount for receipt in year_rec.incomes
              if receipt.income_type == incomes.INCOME_TYPE_OAS)
    assets = sum(fund.amount for fund in self.funds.values())
    gross_income = sum(receipt.amount for receipt in year_rec.incomes) + sum(receipt.amount for receipt in year_rec.withdrawals)
    rrsp_withdrawals = sum(receipt.amount for receipt in year_rec.withdrawals
                           if receipt.fund_type in (funds.FUND_TYPE_RRSP, funds.FUND_TYPE_BRIDGING))
    tfsa_withdrawals = sum(receipt.amount for receipt in year_rec.withdrawals
                           if receipt.fund_type == funds.FUND_TYPE_TFSA)
    nonreg_withdrawals = sum(receipt.amount for receipt in year_rec.withdrawals
                             if receipt.fund_type == funds.FUND_TYPE_NONREG)
    total_withdrawals = rrsp_withdrawals + tfsa_withdrawals + nonreg_withdrawals
    rrsp_deposits = sum(receipt.amount for receipt in year_rec.deposits
                        if receipt.fund_type in (funds.FUND_TYPE_RRSP, funds.FUND_TYPE_BRIDGING))
    tfsa_deposits = sum(receipt.amount for receipt in year_rec.deposits
                        if receipt.fund_type == funds.FUND_TYPE_TFSA)
    nonreg_deposits = sum(receipt.amount for receipt in year_rec.deposits
                          if receipt.fund_type == funds.FUND_TYPE_NONREG)
    savings = rrsp_deposits + tfsa_deposits + nonreg_deposits
    ympe = utils.Indexed(world.YMPE, year_rec.year, 1 + world.PARGE)

    if gross_income < world.LICO_SINGLE_CITY_WP * year_rec.cpi:
      self.gross_income_below_lico_years += 1

    if assets <= 0:
      self.no_assets_years += 1

    if self.age >= world.MINIMUM_RETIREMENT_AGE and not self.retired:
      self.accumulators.earnings_late_working_summary.UpdateOneValue(earnings/cpi)

    if self.retired:
      self.accumulators.lico_gap_retired.UpdateOneValue(max(0, world.LICO_SINGLE_CITY_WP*year_rec.cpi-gross_income)/cpi)
      if assets <= 0:
        self.has_been_ruined=True
        self.accumulators.fraction_retirement_years_ruined.UpdateOneValue(1)
      else:
        self.accumulators.fraction_retirement_years_ruined.UpdateOneValue(0)
      self.accumulators.fraction_retirement_years_below_ympe.UpdateOneValue(1 if assets < ympe else 0)
      self.accumulators.fraction_retirement_years_below_twice_ympe.UpdateOneValue(1 if assets < 2*ympe else 0)
      if gross_income < world.LICO_SINGLE_CITY_WP * year_rec.cpi:
        self.has_experienced_income_under_lico = True
        self.accumulators.fraction_retirement_years_below_lico.UpdateOneValue(1)
      else:
        self.accumulators.fraction_retirement_years_below_lico.UpdateOneValue(0)
      self.accumulators.retirement_taxes.UpdateOneValue(year_rec.taxes_payable/cpi)
      if cpp > 0:
        self.accumulators.positive_cpp_benefits.UpdateOneValue(cpp/cpi)
    else: # Working period
      self.accumulators.lico_gap_working.UpdateOneValue(max(0, world.LICO_SINGLE_CITY_WP*year_rec.cpi-gross_income)/cpi)
      self.accumulators.earnings_working.UpdateOneValue(earnings/cpi)
      self.accumulators.working_annual_ei_cpp_deductions.UpdateOneValue(
          (year_rec.cpp_contribution + year_rec.ei_premium)/cpi)
      self.accumulators.working_taxes.UpdateOneValue(year_rec.taxes_payable/cpi)
      if earnings > 0:
        self.positive_earnings_years += 1
        self.accumulators.fraction_earnings_saved.UpdateOneValue(savings/earnings)
      if ei_benefits > 0:
        self.ei_years += 1
        self.accumulators.positive_ei_benefits.UpdateOneValue(ei_benefits/cpi)

    if self.age >= world.MAXIMUM_RETIREMENT_AGE:
      if gis > 0:
        self.gis_years += 1
        self.has_received_gis = True
        self.accumulators.fraction_retirement_years_receiving_gis.UpdateOneValue(1)
        self.accumulators.positive_gis_benefits.UpdateOneValue(gis/cpi)
      else:
        self.accumulators.fraction_retirement_years_receiving_gis.UpdateOneValue(0)
      self.accumulators.benefits_gis.UpdateOneValue(gis/cpi)

    if not self.basic_only:
      self.accumulators.period_earnings.UpdateOneValue(earnings/cpi, period)
      self.accumulators.period_cpp_benefits.UpdateOneValue(cpp/cpi, period)
      self.accumulators.period_oas_benefits.UpdateOneValue(oas/cpi, period)
      self.accumulators.period_taxable_gains.UpdateOneValue(year_rec.taxable_capital_gains/cpi, period)
      self.accumulators.period_gis_benefits.UpdateOneValue(gis/cpi, period)
      self.accumulators.period_social_benefits_repaid.UpdateOneValue(year_rec.total_social_benefit_repayment/cpi, period)
      self.accumulators.period_rrsp_withdrawals.UpdateOneValue(rrsp_withdrawals/cpi, period)
      self.accumulators.period_tfsa_withdrawals.UpdateOneValue(tfsa_withdrawals/cpi, period)
      self.accumulators.period_nonreg_withdrawals.UpdateOneValue(nonreg_withdrawals/cpi, period)
      self.accumulators.period_cpp_contributions.UpdateOneValue(year_rec.cpp_contribution/cpi, period)
      self.accumulators.period_ei_premiums.UpdateOneValue(year_rec.ei_premium/cpi, period)
      self.accumulators.period_taxable_income.UpdateOneValue(year_rec.taxable_income/cpi, period)
      self.accumulators.period_income_tax.UpdateOneValue(year_rec.taxes_payable/cpi, period)
      self.accumulators.period_sales_tax.UpdateOneValue(year_rec.sales_taxes/cpi, period)
      self.accumulators.period_rrsp_savings.UpdateOneValue(rrsp_deposits/cpi, period)
      self.accumulators.period_tfsa_savings.UpdateOneValue(tfsa_deposits/cpi, period)
      self.accumulators.period_nonreg_savings.UpdateOneValue(nonreg_deposits/cpi, period)
      self.accumulators.period_fund_growth.UpdateOneValue(
          sum(rec.growth_amount for rec in year_rec.growth_records) / cpi, period)

      self.accumulators.persons_alive_by_age.UpdateOneValue(1, self.age)
      self.accumulators.gross_earnings_by_age.UpdateOneValue(earnings/cpi, self.age)
      self.accumulators.income_tax_by_age.UpdateOneValue(year_rec.taxes_payable/cpi, self.age)
      self.accumulators.sales_tax_by_age.UpdateOneValue(year_rec.sales_taxes/cpi, self.age)
      self.accumulators.ei_premium_by_age.UpdateOneValue(year_rec.ei_premium/cpi, self.age)
      self.accumulators.cpp_contributions_by_age.UpdateOneValue(year_rec.cpp_contribution/cpi, self.age)
      self.accumulators.ei_benefits_by_age.UpdateOneValue(ei_benefits/cpi, self.age)
      self.accumulators.cpp_benefits_by_age.UpdateOneValue(cpp/cpi, self.age)
      self.accumulators.oas_benefits_by_age.UpdateOneValue(oas/cpi, self.age)
      self.accumulators.gis_benefits_by_age.UpdateOneValue(gis/cpi, self.age)
      self.accumulators.savings_by_age.UpdateOneValue(savings/cpi, self.age)
      self.accumulators.rrsp_withdrawals_by_age.UpdateOneValue(rrsp_withdrawals/cpi, self.age)
      self.accumulators.tfsa_withdrawals_by_age.UpdateOneValue(tfsa_withdrawals/cpi, self.age)
      self.accumulators.nonreg_withdrawals_by_age.UpdateOneValue(nonreg_withdrawals/cpi, self.age)
      self.accumulators.rrsp_assets_by_age.UpdateOneValue(
          sum(fund.amount for fund in self.funds.values() if fund.fund_type == funds.FUND_TYPE_RRSP)/cpi, self.age)
      self.accumulators.bridging_assets_by_age.UpdateOneValue(
          sum(fund.amount for fund in self.funds.values() if fund.fund_type == funds.FUND_TYPE_BRIDGING)/cpi, self.age)
      self.accumulators.tfsa_assets_by_age.UpdateOneValue(
          sum(fund.amount for fund in self.funds.values() if fund.fund_type == funds.FUND_TYPE_TFSA)/cpi, self.age)
      self.accumulators.nonreg_assets_by_age.UpdateOneValue(
          sum(fund.amount for fund in self.funds.values() if fund.fund_type == funds.FUND_TYPE_NONREG)/cpi, self.age)
      if self.retired:
        self.accumulators.cd_withdrawals_by_age.UpdateOneValue(year_rec.cd_drawdown_amount/cpi, self.age)
        self.accumulators.ced_withdrawals_by_age.UpdateOneValue(year_rec.ced_drawdown_amount/cpi, self.age)

    self.age += 1
    self.year += 1


  def EndOfLifeCalcs(self, year_rec):
    """Calculations that happen upon death"""
    cpi = year_rec.cpi if self.real_values else 1
    if self.retired:
      asset_comparison_level = self.assets_at_retirement
    else:
      asset_comparison_level = sum(fund.amount for fund in self.funds.values()) / year_rec.cpi
    estate = self.CalcEndOfLifeEstate(year_rec)
    self.accumulators.distributable_estate.UpdateOneValue(estate/cpi)
    self.accumulators.fraction_persons_ruined.UpdateOneValue(1 if self.has_been_ruined else 0)
    self.accumulators.fraction_retirees_receiving_gis.UpdateOneValue(1 if self.has_received_gis else 0)
    self.accumulators.fraction_retirees_ever_below_lico.UpdateOneValue(1 if self.has_experienced_income_under_lico else 0)

    self.accumulators.fraction_persons_with_withdrawals_below_retirement_assets.UpdateOneValue(
        1 if self.total_retirement_withdrawals < asset_comparison_level else 0)
    if self.retired:
      self.accumulators.fraction_retirees_with_withdrawals_below_retirement_assets.UpdateOneValue(
          1 if self.total_retirement_withdrawals < asset_comparison_level else 0)
    self.accumulators.lifetime_withdrawals_less_savings.UpdateOneValue(
        (self.total_lifetime_withdrawals - self.total_working_savings)*(year_rec.cpi if not self.real_values else 1))
    self.accumulators.retirement_consumption_less_working_consumption.UpdateOneValue(
        min(0, self.accumulators.retired_consumption_summary.mean - world.FRACTION_WORKING_CONSUMPTION*self.accumulators.working_consumption_summary.mean))

    if not self.basic_only:
      self.accumulators.age_at_death.UpdateOneValue(self.age)
      self.accumulators.years_worked_with_earnings.UpdateOneValue(self.positive_earnings_years)
      self.accumulators.fraction_persons_dying_before_retiring.UpdateOneValue(0 if self.retired else 1)
      self.accumulators.positive_savings_years.UpdateOneValue(self.positive_savings_years)
      self.accumulators.years_receiving_ei.UpdateOneValue(self.ei_years)
      self.accumulators.years_receiving_gis.UpdateOneValue(self.gis_years)
      self.accumulators.years_income_below_lico.UpdateOneValue(self.gross_income_below_lico_years)
      self.accumulators.years_with_no_assets.UpdateOneValue(self.no_assets_years)

      for period in self.period_years:
        self.accumulators.period_years.UpdateOneValue(self.period_years[period], period)
      period = self.Period(year_rec)
      self.accumulators.period_gross_estate.UpdateOneValue(year_rec.gross_estate/cpi, period)
      self.accumulators.period_estate_taxes.UpdateOneValue(year_rec.estate_taxes/cpi, period)
      self.accumulators.period_executor_funeral_costs.UpdateOneValue(year_rec.funeral_and_executor_fee/cpi, period)
      self.accumulators.period_distributable_estate.UpdateOneValue(estate/cpi, period)

  def LiveLife(self):
    """Run through one lifetime"""
    while True:
      year_rec = self.AnnualSetup()
      if not year_rec.is_dead:
        year_rec = self.MeddleWithCash(year_rec)
        self.AnnualReview(year_rec)
      else:
        self.EndOfLifeCalcs(year_rec)
        break


