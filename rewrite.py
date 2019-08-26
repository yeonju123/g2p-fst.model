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
        self, fst: pynini.Fst, token_type: Union[str, pynini.SymbolTable]
    ):
        self.fst = fst
        self.token_type = token_type

    @classmethod
    def from_args(cls, fst_path: str, token_type: str):
        fst = pynini.Fst.read(fst_path)
        return cls(fst, token_type)

    def rewrite(self, i: str) -> str:
        lattice = pynini.acceptor(i, token_type=self.token_type) @ self.fst
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
    rewriter = _Rewriter.from_args(args.fst_path, args.token_type)
    with multiprocessing.Pool() as pool:
        for line in pool.map(rewriter.rewrite, _reader(args.word_path)):
            print(line)


if __name__ == "__main__":
    logging.basicConfig(level="INFO", format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--word_path", required=True, help="path to file of words to rewrite"
    )
    parser.add_argument(
        "--fst_path", required=True, help="path to rewrite fst FST"
    )
    parser.add_argument("--token_type", default="utf8", help="token type")
    main(parser.parse_args())
