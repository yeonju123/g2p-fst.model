#!/usr/bin/env python
""" merge the prediction and gold into a file"""


import argparse
import csv
import logging


def main(args):
    with open(args.gold) as g:
        x = g.read()
    with open(args.hypo) as h:
        y = h.read()
    xline = x.split("\n")
    yline = y.split("\n")
    rows = zip(xline, yline)
    with open(args.output, 'w') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
            


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold", help="Path to gold TSV file")
    parser.add_argument("hypo", help="Path to prediction TSV file")
    parser.add_argument("output", help="Path to output TSV file")
    main(parser.parse_args())