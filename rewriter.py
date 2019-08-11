#!/usr/bin/env python
"""Rewrites FST examples.

This script assumes the input is provided one example per line."""

import argparse
import logging
import multiprocessing

from typing import Iterator, Union

import pynini


class _Rewriter:
    """Helper object for rewriting."""

    def __init__(
        self, rule: pynini.Fst, token_type: Union[str, pynini.SymbolTable]
    ):
        self.rule = rule
        self.token_type = token_type

    @classmethod
    def from_args(cls, rule_path: str, token_type: str):
        rule = pynini.Fst.read(rule_path)
        # Either it's one of the two standard ones or it's a symbol table path.
        if token_type in ("byte", "token"):
            _token_type = token_type
        else:
            _token_type = pynini.SymbolTable.read_text(token_type)
        return cls(rule, _token_type)

    def rewrite(self, i: str) -> str:
        lattice = pynini.acceptor(i, token_type=self.token_type) @ self.rule
        if lattice.start() == pynini.NO_STATE_ID:
            logging.error("Composition failure: %s", i)
            return "<composition failure>"
        return pynini.shortestpath(lattice).stringify(
            token_type=self.token_type
        )


def _reader(path: str) -> Iterator[str]:
    """Reads strings from a single-column filepath."""
    with open(path, "r") as source:
        for line in source:
            yield line.rstrip()


def main(args: argparse.Namespace) -> None:
    rewriter = _Rewriter.from_args(args.rule_path, args.token_type)
    with multiprocessing.Pool() as pool:
        for line in pool.map(rewriter.rewrite, _reader(args.word_path)):
            print(line)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--word_path", required=True, help="Path to file of words to rewrite"
    )
    parser.add_argument(
        "--rule_path", required=True, help="Path to rewrite rule FST"
    )
    parser.add_argument(
        "--token_type",
        default="byte",
        help='Token type ("byte", "utf8") '
        "or path to symbol table (default: %(default)s)",
    )
    main(parser.parse_args())
