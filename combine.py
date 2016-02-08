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
  for line in f:
    line = line.strip()
    if not line:
      break

    row = line.split(',')
    col.append(row[1])
  t.append(col)

w = csv.writer(sys.stdout)
for row in zip(*t):
  w.writerow(row)
