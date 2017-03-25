"""Copies fitness values from multiple optimization runs into one CSV file with one run per column."""

import argparse
import csv
import logging
import sys

parser = argparse.ArgumentParser(description='Copy fitness values into one CSV table')
parser.add_argument('files', metavar='file', type=open, nargs='+', help='file to extract fitness values from')

args = parser.parse_args()

t = []
for f in args.files:
  header = next(f)
  if header != "Generation,Best Fitness,Fitness Mean,Fitness Stddev,Best Individual ID\n":
    logging.warning("%s does not appear to contain fitness values", f.name)
    continue

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

  t.append(col)

# Insert what will become the header column in the table once it's transposed
header_row = ['Gen %d' % i for i in range(len(t[0])-1)] + ['Final']
t.insert(0, header_row)

w = csv.writer(sys.stdout)
for row in zip(*t):
  w.writerow(row)
