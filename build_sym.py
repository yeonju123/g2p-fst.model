#!/usr/bin/env python

"""Compiles a SymbolTable from TSV file."""

import argparse
import json
import unicodedata

from typing import List, FrozenSet

import pynini


def _char_processor(token: str) -> List[str]:

    """Returns a list of characters with unseparated diacritics
    """
    MODS = frozenset(
        {
            "ˡ",
            "ˍ",
            "ʲ",
            "ˠ",
            "˺",
            "ː",
            "˞",
            "˽",
            "ˬ",
            "˖",
            "ʰ",
            "ˤ",
            "˳",
            "˟",
            "ⁿ",
            "ʷ",
            "˕",
            "ˌ",
            "˷",
            "˔",
        }
    )
    chars = []
    for char in token:
        # Keep combining characters together
        if unicodedata.combining(char) or char in MODS:
            m = chars.pop()
            chars.append(f"{m}{char}")
        else:
            chars.append(char)
    return chars


def main(args: argparse.Namespace) -> None:

    syms = set()
    with open(args.input_lexicon, "r") as src:
        for line in src:
            normline = unicodedata.normalize("NFC", line.strip())
            ortho, phon = normline.split("\t")
            syms.update(_char_processor(ortho))
            syms.update(_char_processor(phon))

    sym = pynini.SymbolTable()
    key = 0
    sym.add_symbol(symbol="<eps>", key=key)
    for s in syms:
        key += 1
        sym.add_symbol(s, key)

    sym.write_text(args.output_sym)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input_lexicon", required=True, help="input TSV file path"
    )
    parser.add_argument(
        "--output_sym", required=True, help="output SymbolTable file path"
    )
    main(parser.parse_args())
