import argparse
import csv
import glob
import logging
import os.path
import statistics
import sys

OLDNORMAL_BRANCHES = ('halfympe', 'ympe', 'twiceympe')
NEWNORMAL_BRANCHES = ('halfympe_newnormal', 'ympe_newnormal', 'twiceympe_newnormal')
PERSONALITIES = ('earth', 'air', 'fire', 'water')
LABELS = ('Average Fraction of Earnings Saved', 'ConsumptionAvgLifetime', 'ConsumptionAvgWorking', 'ConsumptionAvgRetired', 'Average Net Government Revenue', 'Distributable Estate')

parser = argparse.ArgumentParser(description='Copy fitness values into one CSV table')
parser.add_argument('dir', type=str, help='Directory containing CSV files to extract strategy values from')
args = parser.parse_args()

def extract_values(filename):
  """Extracts fraction of earnings saved, consumption, net government revenue, and estate"""
  v = {}
  with open(filename, 'r') as f:
    for line in f:
      fields = line.strip().split(',')
      if fields[0] in LABELS:
        v[fields[0]] = float(fields[1])
  return tuple(v.get(k, 0) for k in LABELS)

def values_across_files(directory, branch, personality):
  name_pattern = os.path.join(directory, 'opt_%s_%s_*.csv' % (branch, personality))
  files = glob.glob(name_pattern)
  if not files:
    logging.warning('No files found for %s' % name_pattern)
    return (0,0,0,0,0,0)
  return tuple(statistics.mean(col) for col in zip(*[extract_values(f) for f in files]))

t = []

# Header column
h = ['']
for label in LABELS:
  h.append(label + ' old normal')
  h.append(label + ' new normal')
  h.append(label + ' diff')
t.append(h)

# Data columns
for i, branch in enumerate(OLDNORMAL_BRANCHES):
  for p in PERSONALITIES:
    c = [p + ' ' + branch]
    old = values_across_files(args.dir, branch, p)
    new = values_across_files(args.dir, NEWNORMAL_BRANCHES[i], p)
    for j in range(len(old)):
      c.append(old[j])
      c.append(new[j])
      c.append(old[j]-new[j])
    t.append(c)

# output
w = csv.writer(sys.stdout)
for row in zip(*t):
  w.writerow(row)
