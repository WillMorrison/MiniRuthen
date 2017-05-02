"""Combiner script for input to box and whisker plots."""

import argparse
import collections
import csv
import glob
import logging
import os.path
import sys

parser = argparse.ArgumentParser(description='Copy fitness values into one CSV table')
parser.add_argument('dir', type=str, help='Directory containing CSV files to extract strategy values from')
parser.add_argument('columns', type=str, nargs='+', help='List of file prefixes to use for columns')
parser.add_argument('--normalize', default=True, action='store_false', help='Whether to normalize strategy components')
args = parser.parse_args()

# Map of strategy parameter name in the raw CSV files to output value
STRATEGY_PARAMETERS = collections.OrderedDict([
  ('Planned Retirement Age', 'RetirementAge'),
  ('Savings Threshold', 'SaveThresh'),
  ('Savings Rate', 'SaveRate'),
  ('Savings RRSP Fraction', 'SaveRRSPFrac'),
  ('Savings TFSA Fraction', 'SaveTFSAFrac'),
  ('Working Period Drawdown TFSA Fraction', 'WorkingTFSAFrac'),
  ('Working Period Drawdown NonReg Fraction', 'WorkingNonRegFrac'),
  ('OAS Bridging Fraction', 'OASFrac'),
  ('Drawdown CED Fraction', 'CEDFrac'),
  ('Initial CD Fraction', 'CDFrac'),
  ('Drawdown Preferred RRSP Fraction', 'RetiredRRSPFrac'),
  ('Drawdown Preferred TFSA Fraction', 'RetiredTFSAFrac'),
])

STRATEGY_BOUNDS = {
    'Planned Retirement Age': (60, 65),  # planned_retirement_age
    'Savings Threshold': (0, 1.5),  # savings_threshold
    'Savings Rate': (0, 0.5),  # savings_rate
    'Savings RRSP Fraction': (0, 1),  # savings_rrsp_fraction
    'Savings TFSA Fraction': (0, 1),  # savings_tfsa_fraction
    'Working Period Drawdown TFSA Fraction': (0, 1),  # working_period_drawdown_tfsa_fraction
    'Working Period Drawdown NonReg Fraction': (0, 1),  # working_period_drawdown_nonreg_fraction
    'OAS Bridging Fraction': (0, 5),  # oas_bridging_fraction
    'Drawdown CED Fraction': (0, 1),  # drawdown_ced_fraction
    'Initial CD Fraction': (0, 1),  # initial_cd_fraction
    'Drawdown Preferred RRSP Fraction': (0, 1),  # drawdown_preferred_rrsp_fraction
    'Drawdown Preferred TFSA Fraction': (0, 1),  # drawdown_preferred_tfsa_fraction
}

def StrategyFromFile(filename, norm):
  sd = {}
  with open(filename, 'r') as f:
    # read forward to the strategy vector table
    for line in f:
      if line.startswith('parameter,value'):
        break
    else:
      raise ValueError("%s does not appear to contain a strategy vector" % f.name)

    for line in f:
      line = line.strip()
      if not line:
        break
      param, val = line.split(',')
      if param in STRATEGY_PARAMETERS:
        if norm:
          sd[param] = (float(val)-STRATEGY_BOUNDS[param][0])/(STRATEGY_BOUNDS[param][1]-STRATEGY_BOUNDS[param][0])
        else:
          sd[param] = val

  return sd

def MakeBlock(filenames, i, norm):
  logging.info('Making block %d from %r' % (i, filenames))
  strategies = [StrategyFromFile(name, norm) for name in filenames]
  block = [[i] + ['']*(len(STRATEGY_PARAMETERS)-1),
           [STRATEGY_PARAMETERS[param] for param in STRATEGY_PARAMETERS]]
  for strategy in strategies:
    block.append([strategy[param] for param in STRATEGY_PARAMETERS])
  return zip(*block)

filenames_for_column = collections.OrderedDict()
for column in args.columns:
  filenames_for_column[column] = glob.glob(os.path.join(args.dir, column) + '_*.csv')
  logging.info('Found %d files for %s' % (len(filenames_for_column[column]), column))

w = csv.writer(sys.stdout)
w.writerow(['', ''] + args.columns)
for i, block_filenames in enumerate(zip(*filenames_for_column.values())):
  for row in MakeBlock(block_filenames, i, args.normalize):
    w.writerow(row)

