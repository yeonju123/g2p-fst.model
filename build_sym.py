#!/usr/bin/env python

"""Compiles a SymbolTable from TSV file."""

import argparse
import unicodedata

from typing import List

import pynini


def _char_processor(token: str) -> List[str]:
    """Returns a list of characters with unseparated diacritics."""
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

    table = pynini.SymbolTable()
    table.add_symbol(symbol="<epsilon>")
    for s in syms:
        table.add_symbol(s)

    table.write_text(args.output_sym)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input_lexicon", required=True, help="input TSV file path"
    )
    parser.add_argument(
        "--output_sym", required=True, help="output SymbolTable file path"
    )
    main(parser.parse_args())
