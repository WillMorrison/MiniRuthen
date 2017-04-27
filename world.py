# Parameter/Constant definitions for mini-Ruthen

import collections

# Unless otherwise noted, all dollar amounts are real dollar amounts

# The year at which subject turns 30 and the simulated lifetime starts
BASE_YEAR = 2014
START_AGE = 30

# Inflation parameters
INFLATION_MEAN = 0.02 # Average annual inflation
INFLATION_STDDEV = 0.007 # Standard deviation of annual inflation

# OAS (Old Age Security benefit) Parameters
OAS_BENEFIT = 6676.69 # Full-year OAS benefit, 2014 and subsequent years; nominal, indexed by personal CPI
OAS_CLAWBACK_EXEMPTION = 71592 # Income level beyond which OAS gets clawed back, all years; nominal, indexed by personal CPI
OAS_CLAWBACK_RATE = 0.15 # OAS is reduced by this fraction of income in excess of OAS_CLAWBACK_EXEMPTION

# GIS (Guaranteed Income Security benefit) Parameters
GIS_SINGLES_RATE = 9015.37 # GIS maximum benefit (2014) for a senior with no other income; nominal, indexed by personal CPI
GIS_CLAWBACK_EXEMPTION = 12 # GIS is reduced in respect of income above this level; constant for all years
GIS_REDUCTION_RATE = 0.5 # GIS is reduced by this fraction of income above GIS_CLAWBACK_EXEMPTION
GIS_SUPPLEMENT_EXEMPTION = 4431.28 # GIS supplement is reduced in respect of income above this level; nominal, indexed by personal CPI
GIS_SUPPLEMENT_MAXIMUM = 910.27 # GIS supplement maximum benefit (2014) for a senior with no other income; nominal, indexed by personal CPI
GIS_SUPPLEMENT_REDUCTION_RATE = 0.25 # GIS supplement is reduced by this fraction of income above GIS_SUPPLEMENT_EXEMPTION

# CPP (Canada Pension Plan) Parameters
YMPE = 52500 # Year's Maximum Pensionable Earnings in 2014, indexed by personal CPI and for real wage growth (1+PARGE)
YBE = 3500 # Year's Basic Exemption; CPP contributions are payable on earnings between YBE and YMPE. Nominal value, constant for all years.
MPEA_YEARS = 5 # Number of years over which to calculate the moving average of YMPE
CPP_EMPLOYEE_RATE = 0.0495 # CPP Contribution Rate, Employee component
CPP_EXPECTED_RETIREMENT_AGE = 65 # Age at which there is no actuarial adjustment to the CPP benefits
AAF_PRE65 = 0.072 # CPP actuarial adjustment factor for early retirement - ages 60 - 64, benefit decrement per year
AAF_POST65 = 0.084 # CPP actuarial adjustment factor for delayed retirement, after age 65, benefit increment per year
AAF_POST65_YEARS_CAP = 5 # Years after retirement that delayed retirement benefit increment per year caps at
CPP_GENERAL_DROPOUT_FACTOR = 0.17 # CPP general dropout fraction: fraction of the earnings years that can be dropped out
CPP_RETIREMENT_BENEFIT_FRACTION = 0.25 # CPP fraction of earnings replaced (capped)
CPP_DEATH_BENEFIT = 2500 # nominal value, constant for all years
EARNINGS_YMPE_FRACTION = 1
PRE_SIM_CPP_YEARS = START_AGE - 18
PRE_SIM_ZERO_EARNING_YEARS = 4
PRE_SIM_POSITIVE_EARNING_YEARS = 8
PRE_SIM_SUM_YMPE_FRACTIONS = 6
PRE_SIM_YMPE_FRACTIONS = [0]*PRE_SIM_ZERO_EARNING_YEARS + [PRE_SIM_SUM_YMPE_FRACTIONS/PRE_SIM_POSITIVE_EARNING_YEARS]*PRE_SIM_POSITIVE_EARNING_YEARS

# EI (Employment Insurance) parameters
EI_MAX_INSURABLE_EARNINGS = 48600 # Maximum Insurable Earnings in 2014; nominal, indexed by personal CPI, and for real wage growth (1+PARGE)
EI_BENEFIT_FRACTION = 0.55 # EI benefits for the unemployed are this fraction of the previous year's earnings
EI_PREMIUM_RATE = 0.0192 # Employment Insurance Premium Rate, all years
EI_REPAYMENT_BASE_FRACTION = 1.25 # Fraction of EI_MAX_INSURABLE_EARNINGS; income beyond this leads to EI benefit repayment
EI_REPAYMENT_REDUCTION_RATE = 0.3 # EI benefit is clawed back at this rate for every dollar of income beyond 
                                  # EI_REPAYMENT_BASE_FRACTION * EI_MAX_INSURABLE_EARNINGS
EI_PREINITIAL_YEAR_INSURABLE_EARNINGS = min(EARNINGS_YMPE_FRACTION * YMPE, EI_MAX_INSURABLE_EARNINGS) # Insurable earnings for the year prior to the base year
								  
# RRSP (Registered Retirement Savings Plan) Parameters (also RRIF after age 71)
RRSP_LIMIT = 24270 # Maximum NEW RRSP room in a year; contributions are permitted up to the level of RRSP room; nominal, indexed by personal CPI and real wage growth (1+PARGE)
RRSP_INITIAL_LIMIT = 50000 # Initial RRSP room upon starting the fund in 2014; maintained in nominal terms by the program for new room and contributions
RRSP_ACCRUAL_FRACTION = 0.18 # New RRSP contribution room is based on this fraction of the PREVIOUS year's earnings

class ExtendedDict(collections.defaultdict):
  """This acts like a dictionary, but will return the values for minimum and maximum keys for keys outside that range"""
  def __missing__(self, key):
    if key > max(self.keys()):
      return self[max(self.keys())]
    elif key < min(self.keys()):
      return self[min(self.keys())]
    else:
      return self.Interpolate(key)

  def Interpolate(self, key):
    raise KeyError("Don't know how to interpolate")


# Required Minimum Withdrawal Fraction of BoY balance by age (ages 71+)
MINIMUM_WITHDRAWAL_FRACTION = ExtendedDict(None,
    [(70, 0),
     (71, 0.0528),
     (72, 0.0540),
     (73, 0.0553),
     (74, 0.0567),
     (75, 0.0582),
     (76, 0.0598),
     (77, 0.0617),
     (78, 0.0636),
     (79, 0.0658),
     (80, 0.0682),
     (81, 0.0708),
     (82, 0.0738),
     (83, 0.0771),
     (84, 0.0808),
     (85, 0.0851),
     (86, 0.0899),
     (87, 0.0955),
     (88, 0.1021),
     (89, 0.1099),
     (90, 0.1192),
     (91, 0.1306),
     (92, 0.1449),
     (93, 0.1634),
     (94, 0.1879),
     (95, 0.2000)])

# TFSA (Tax-Free Savings Account) Parameters
TFSA_ANNUAL_CONTRIBUTION_LIMIT = 5500 # Annual new TFSA contribution room in 2014 and subsequently; nominal, indexed by personal CPI
TFSA_INITIAL_CONTRIBUTION_LIMIT = 40000 # Contribution room when the TFSA fund starts in 2014. TFSA room is maintained by the program for contributions and new room.


# Income Tax Parameters
# Federal Income Tax Schedule (Basic federal tax as a function of taxable income, with interpolation)

class TaxSchedule(ExtendedDict):
  def Interpolate(self, key):
   key_b = max(e_key for e_key in self.keys() if e_key < key)
   key_t = min(e_key for e_key in self.keys() if e_key > key)
   p = (key-key_b)/(key_t-key_b)
   return self[key_b] + p * (self[key_t]-self[key_b])


FEDERAL_TAX_SCHEDULE = TaxSchedule(None, # Both the ordinate and abscissa values are scaled by personal CPI
[(0, 0),
 (43953, 6593),
 (87907, 16263),
 (136270, 28837),
 (10136270, 2928837)])

PROVINCIAL_TAX_FRACTION = 0.41 # Should be 0.39 for half-YMPE, 0.41 for YMPE, and 0.53 for twice-YMPE

# End of life probate tax parameters
PROBATE_RATE_CHANGE_LEVEL = 50000 # Treated as constant nominal value for all simulation years, i.e., not indexed
PROBATE_RATE_ABOVE = 0.015
PROBATE_RATE_BELOW = 0.005
EXECUTOR_COST_FRACTION = 0.02
FUNERAL_COST = 10000 # nominal, indexed by personal CPI

# Credit-related
BASIC_PERSONAL_AMOUNT = 11138 # Basic Personal Amount for federal non-refundable income tax credits; nominal, indexed by personal CPI
AGE_AMOUNT_MAXIMUM = 6916 # Maximum Age Amount for federal non-refundable income tax credits; nominal, indexed by personal CPI
AGE_AMOUNT_EXEMPTION = 34873 # The age amount is reduced by income in excess of this amount; nominal, indexed by personal CPI
AGE_AMOUNT_REDUCTION_RATE = 0.15 # The age amount is reduced by this fraction of income in excess of AGE_AMOUNT_EXEMPTION
PENSION_AMOUNT_MAXIMUM = 2000 # A pension credit is claimable for pension income up to this amount; treated as nominal (unindexed) for all years

# Social Benefit Repayment Parameters
SBR_BASE_AMOUNT = 71592 # For income in excess of this amount, social benefits are reduced (clawed back); nominal, indexed by personal CPI
SBR_REDUCTION_RATE = 0.15 # Social benefits are reduced by this fraction of income in excess of SBR_BASE_AMOUNT

# Other Federal Income Tax Parameters
CG_INCLUSION_RATE = 0.5 # Capital Gains Inclusion Rate (proportion of realized capital gains that is taxed)
DIVIDEND_GROSSUP_RATE = 1.38 # Dividend gross-up rate: multiplier for actual dividends to get taxable dividends
DIVIDEND_TAX_CREDIT_RATE = 0.150198 # Fraction of dividends claimable as a non-refundable dividend tax credit
NON_REFUNDABLE_CREDIT_RATE = 0.15 # Equal to the rate at the lowest tax bracket

# Economic Parameters
MEAN_INVESTMENT_RETURN = 0.0266 # Mean of normal distribution for returns to funds.
STD_INVESTMENT_RETURN = 0.02 # Standard deviation for normal distribution for returns to funds
IMMEDIATELY_REALIZED_GAINS_FRACTION = 0.3 # Fraction of new growth that is immediately realized 
UNREALIZED_GAINS_REALIZATION_FRACTION = 0.2 # Fraction of unrealized gains that become realized each year

# Other Miscellaneous Parameters
LICO_SINGLE_CITY_WP = 24312 # Low Income Cut-Off; nominal, indexed by personal CPI
SALES_TAX_EXEMPTION = 8000 # Assumed amount of spending deemed NOT subject to HST sales tax; nominal, indexed by personal CPI
HST_RATE = 0.13 # Harmonized Sales Tax rate is the sum of 0.05 GST rate(federal) and 0.08 PST rate(provincial)
DISCOUNT_RATE = 0.03 # Annual discount rate applied to consumption to reflect time preference
PARGE = 0.01 # Projected annual real growth in earnings
YMPE_STDDEV = 0.1 # Standard deviation for earnings as a fraction of current YMPE
AVG_DISABILITY_AGE = 77 # Age after which subject is considered likely disabled

MALE_MORTALITY = ExtendedDict(None,
[(0, 0.00577),
 (1, 0.00035),
 (2, 0.00021),
 (3, 0.00021),
 (4, 0.00020),
 (5, 0.00017),
 (6, 0.00013),
 (7, 0.00009),
 (8, 0.00008),
 (9, 0.00008),
 (10, 0.00010),
 (11, 0.00010),
 (12, 0.00015),
 (13, 0.00023),
 (14, 0.00034),
 (15, 0.00046),
 (16, 0.00057),
 (17, 0.00066),
 (18, 0.00072),
 (19, 0.00078),
 (20, 0.00082),
 (21, 0.00085),
 (22, 0.00087),
 (23, 0.00087),
 (24, 0.00085),
 (25, 0.00083),
 (26, 0.00081),
 (27, 0.00080),
 (28, 0.00082),
 (29, 0.00084),
 (30, 0.00088),
 (31, 0.00091),
 (32, 0.00096),
 (33, 0.00100),
 (34, 0.00105),
 (35, 0.00110),
 (36, 0.00116),
 (37, 0.00123),
 (38, 0.00132),
 (39, 0.00141),
 (40, 0.00152),
 (41, 0.00164),
 (42, 0.00178),
 (43, 0.00195),
 (44, 0.00213),
 (45, 0.00233),
 (46, 0.00255),
 (47, 0.00279),
 (48, 0.00304),
 (49, 0.00331),
 (50, 0.00360),
 (51, 0.00394),
 (52, 0.00434),
 (53, 0.00481),
 (54, 0.00533),
 (55, 0.00590),
 (56, 0.00654),
 (57, 0.00726),
 (58, 0.00805),
 (59, 0.00890),
 (60, 0.00982),
 (61, 0.01085),
 (62, 0.01198),
 (63, 0.01321),
 (64, 0.01451),
 (65, 0.01593),
 (66, 0.01752),
 (67, 0.01930),
 (68, 0.02124),
 (69, 0.02329),
 (70, 0.02555),
 (71, 0.02810),
 (72, 0.03104),
 (73, 0.03429),
 (74, 0.03779),
 (75, 0.04165),
 (76, 0.04599),
 (77, 0.05091),
 (78, 0.05631),
 (79, 0.06210),
 (80, 0.06846),
 (81, 0.07555),
 (82, 0.08353),
 (83, 0.09214),
 (84, 0.10129),
 (85, 0.11135),
 (86, 0.12268),
 (87, 0.13566),
 (88, 0.15005),
 (89, 0.16558),
 (90, 0.18264),
 (91, 0.20160),
 (92, 0.22283),
 (93, 0.22086),
 (94, 0.23867),
 (95, 0.25754),
 (96, 0.27751),
 (97, 0.29858),
 (98, 0.32077),
 (99, 0.34406),
 (100, 0.36846),
 (101, 0.39396),
 (102, 0.42053),
 (103, 0.44815),
 (104, 0.47678),
 (105, 0.50637),
 (106, 0.53687),
 (107, 0.56822),
 (108, 0.60036),
 (109, 0.63320),
 (110, 1.0)])

FEMALE_MORTALITY = ExtendedDict(None,
[(0, 0.00467),
 (1, 0.00035),
 (2, 0.00020),
 (3, 0.00015),
 (4, 0.00012),
 (5, 0.00010),
 (6, 0.00008),
 (7, 0.00007),
 (8, 0.00007),
 (9, 0.00007),
 (10, 0.00009),
 (11, 0.00009),
 (12, 0.00013),
 (13, 0.00016),
 (14, 0.00020),
 (15, 0.00024),
 (16, 0.00028),
 (17, 0.00031),
 (18, 0.00033),
 (19, 0.00034),
 (20, 0.00034),
 (21, 0.00034),
 (22, 0.00034),
 (23, 0.00033),
 (24, 0.00033),
 (25, 0.00033),
 (26, 0.00033),
 (27, 0.00033),
 (28, 0.00035),
 (29, 0.00037),
 (30, 0.00039),
 (31, 0.00042),
 (32, 0.00046),
 (33, 0.00050),
 (34, 0.00055),
 (35, 0.00061),
 (36, 0.00067),
 (37, 0.00073),
 (38, 0.00079),
 (39, 0.00085),
 (40, 0.00092),
 (41, 0.00099),
 (42, 0.00109),
 (43, 0.00120),
 (44, 0.00132),
 (45, 0.00145),
 (46, 0.00160),
 (47, 0.00176),
 (48, 0.00193),
 (49, 0.00210),
 (50, 0.00229),
 (51, 0.00251),
 (52, 0.00276),
 (53, 0.00305),
 (54, 0.00337),
 (55, 0.00372),
 (56, 0.00410),
 (57, 0.00451),
 (58, 0.00494),
 (59, 0.00538),
 (60, 0.00587),
 (61, 0.00641),
 (62, 0.00704),
 (63, 0.00774),
 (64, 0.00850),
 (65, 0.00933),
 (66, 0.01026),
 (67, 0.01131),
 (68, 0.01243),
 (69, 0.01362),
 (70, 0.01493),
 (71, 0.01645),
 (72, 0.01823),
 (73, 0.02019),
 (74, 0.02230),
 (75, 0.02467),
 (76, 0.02742),
 (77, 0.03066),
 (78, 0.03424),
 (79, 0.03807),
 (80, 0.04240),
 (81, 0.04748),
 (82, 0.05354),
 (83, 0.06068),
 (84, 0.06872),
 (85, 0.07755),
 (86, 0.08703),
 (87, 0.09704),
 (88, 0.10767),
 (89, 0.11899),
 (90, 0.13088),
 (91, 0.14322),
 (92, 0.15588),
 (93, 0.17087),
 (94, 0.18680),
 (95, 0.20376),
 (96, 0.22177),
 (97, 0.24083),
 (98, 0.26094),
 (99, 0.28209),
 (100, 0.30425),
 (101, 0.32740),
 (102, 0.35151),
 (103, 0.37651),
 (104, 0.40237),
 (105, 0.42902),
 (106, 0.45638),
 (107, 0.48439),
 (108, 0.51296),
 (109, 0.54200),
 (110, 1.0)])

MORTALITY_MULTIPLIER = 1 # Multiplier for mortality probabilities ( > 1.0 => more likely than usual to die)

# CED Drawdown table calculations
def GenerateCEDDrawdownTable(index_min, index_max):
  _r = (1 + INFLATION_MEAN) / ((1 + MEAN_INVESTMENT_RETURN) * (1 + INFLATION_MEAN))
  _boy_fund = (1-_r**(index_max - index_min))/(1-_r)
  _table_items = []
  for i, age in enumerate(range(index_min, index_max)):
    _boy_payment = (1 + INFLATION_MEAN)**i
    _table_items.append((age, _boy_payment/_boy_fund))
    _boy_fund = (_boy_fund - _boy_payment) * ( 1 + MEAN_INVESTMENT_RETURN) * (1 + INFLATION_MEAN)
  return ExtendedDict(None, _table_items)

CED_TABLE_MIN_AGE = 60
CED_TABLE_MAX_AGE = 111
CED_PROPORTION = GenerateCEDDrawdownTable(CED_TABLE_MIN_AGE, CED_TABLE_MAX_AGE)

# Fate
INVOLUNTARY_RETIREMENT_INCREMENT = 0.08
MINIMUM_RETIREMENT_AGE = 60
MAXIMUM_RETIREMENT_AGE = 65
UNEMPLOYMENT_PROBABILITY = 0.08

# Fitness component constants
FRACTION_WORKING_CONSUMPTION = 0.8
