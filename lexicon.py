#!/usr/bin/env python
"""Compiles FAR lexicons from TSV file."""


import argparse
import logging
import pynini
import pywrapfst as fst


def main(args):
    with open(args.input_path, "r") as source:
        g_writer = fst.FarWriter.create(args.g_far_path)
        p_writer = fst.FarWriter.create(args.p_far_path)
        for (linenum, line) in enumerate(source, 1):
            key = f"{linenum:08x}"
            (g, p) = line.rstrip().split("\t", 1)
            g_acceptor = pynini.acceptor(g, token_type=args.token_type)
            g_compact = fst.convert(g_acceptor, "compact_string")
            g_writer[key] = g_compact
            p_acceptor = pynini.acceptor(p, token_type=args.token_type)
            p_compact = fst.convert(p_acceptor, "compact_string")
            p_writer[key] = p_compact
        logging.info("Processed g and p pairs:\t%d pairs", linenum)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input_path", required=True, help="input TSV file path"
    )
    parser.add_argument(
        "--g_far_path", required=True, help="output grapheme FAR path"
    )
    parser.add_argument(
        "--p_far_path", required=True, help="output phoneme FAR path"
    )
    parser.add_argument(
        "--token_type", default="utf8", help="token type for acceptors"
    )
    main(parser.parse_args())
