"""Script to count the number of result files for each personality/environment combination, assuming the standard naming convention."""

import argparse
import glob

parser = argparse.ArgumentParser(description='Copy fitness values into one CSV table')
parser.add_argument('dir', type=str, help='Directory containing CSV files to extract strategy values from')
args = parser.parse_args()

BRANCHES = ('ympe', 'ympe_newnormal', 'halfympe', 'halfympe_newnormal', 'twiceympe', 'twiceympe_newnormal')
ELEMENTS = ('earth', 'air', 'fire', 'water')

for b in BRANCHES:
  for e in ELEMENTS:
    print('%s_%s: %d' % (b, e, len(glob.glob('%s/opt_%s_%s*.csv' % (args.dir, b, e)))))

