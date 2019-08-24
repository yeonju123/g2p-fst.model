#!/usr/bin/env python
"""Performs a 80-10-10 split of the data.
This script is totally agnostic to the data format, except that it assumes one
example per line."""


import argparse
import logging
import random


def main(args: argparse.Namespace) -> None:
    # Reads in data and shuffles.
    with open(args.input_path, "r") as source:
        data = [line.rstrip() for line in source]
    random.seed(args.seed)
    random.shuffle(data)
    # Creates split boundaries.
    train_right = int(len(data) * 0.8)
    dev_right = int(len(data) * 0.9)
    # Writes them out.
    subset = data[:train_right]
    logging.info("Train set:\t%d lines", len(subset))
    with open(args.train_path, "w") as sink:
        for line in subset:
            print(line, file=sink)
    subset = data[train_right:dev_right]
    logging.info("Development set:\t%d lines", len(subset))
    with open(args.g_dev_path, "w") as sink:
        for line in subset:
            line = line.split('\t')[0]
            print(line, file=sink)
    with open(args.p_dev_path, "w") as sink:
        for line in subset:
            line = line.split('\t')[1]
            print(line, file=sink)
    subset = data[dev_right:]
    logging.info("Test set:\t\t%d lines", len(subset))
    with open(args.g_test_path, "w") as sink:
        for line in subset:
            line = line.split('\t')[0]
            print(line, file=sink)
    with open(args.p_test_path, "w") as sink:
        for line in subset:
            line = line.split('\t')[1]
            print(line, file=sink)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for shuffling data",
    )
    parser.add_argument("--input_path", required=True, help="Input data path")
    parser.add_argument(
        "--train_path", required=True, help="Output training data path"
    )
    parser.add_argument(
        "--g_dev_path", required=True, help="Output grapheme development data path"
    )
    parser.add_argument(
        "--p_dev_path", required=True, help="Output phoneme development data path"
    )
    parser.add_argument(
        "--g_test_path", required=True, help="Output grapheme test data path"
    )
    parser.add_argument(
        "--p_test_path", required=True, help="Output phoneme test data path"
    )
    main(parser.parse_args())