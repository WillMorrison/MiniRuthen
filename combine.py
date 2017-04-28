"""Copies fitness values from multiple optimization runs into one CSV file with one run per column."""

import argparse
import csv
import logging
import sys

parser = argparse.ArgumentParser(description='Copy fitness values into one CSV table')
parser.add_argument('files', metavar='file', type=open, nargs='+', help='file to extract fitness values from')
parser.add_argument('--extract_strategies', action='store_true', default=False, help='Extract strategy vectors instead of fitness values')
parser.add_argument('--transpose', action='store_false', default=True, help='Transpose table before outputting')

args = parser.parse_args()

STRATEGY_PARAMETERS = [
  'Planned Retirement Age',
  'Savings Threshold',
  'Savings Rate',
  'Savings RRSP Fraction',
  'Savings TFSA Fraction',
  'Working Period Drawdown TFSA Fraction',
  'Working Period Drawdown NonReg Fraction',
  'OAS Bridging Fraction',
  'Drawdown CED Fraction',
  'Initial CD Fraction',
  'Drawdown Preferred RRSP Fraction',
  'Drawdown Preferred TFSA Fraction',
  'Fitness Function Value',
]

def extract_fitness(f):
  header = next(f)
  if header != "Generation,Best Fitness,Fitness Mean,Fitness Stddev,Best Individual ID\n":
    raise ValueError("%s does not appear to contain fitness values" % f.name)

  col = []
  # Copy the fitness values during the optimization
  for line in f:
    line = line.strip()
    if not line:
      break

    row = line.split(',')
    col.append(row[1])
  # Find the final run's fitness value and copy it in last
  for line in f:
    line = line.strip()
    if line.startswith('Fitness Function Value,'):
      row = line.split(',')
      col.append(row[1])
      break

  return col

def extract_strategy(f):
  sd = {}
  # read forward to the strategy vector table
  for line in f:
    if line.startswith('parameter,value'):
      break
    elif line.startswith('Fitness Function Value'):
      line = line.strip()
      param, val = line.split(',')
      sd[param] = val
  else:
    raise ValueError("%s does not appear to contain a strategy vector" % f.name)

  for line in f:
    line = line.strip()
    if not line:
      break
    param, val = line.split(',')
    sd[param] = val

  return [sd[param] for param in STRATEGY_PARAMETERS]

# Extract columns of values from each file
t = []
for f in args.files:
  try:
    if args.extract_strategies:
      t.append(extract_strategy(f))
    else:
      t.append(extract_fitness(f))
  except ValueError as e:
    logging.warning(e)

# Insert what will become the header column in the table once it's transposed
if args.extract_strategies:
  header_row = STRATEGY_PARAMETERS
else:
  header_row = ['Gen %d' % i for i in range(len(t[0])-1)] + ['Final']
t.insert(0, header_row)

w = csv.writer(sys.stdout)
if args.transpose:
  for row in zip(*t):
    w.writerow(row)
else:
  for row in t:
    w.writerow(row)
