#!/usr/bin/env python

"""Compiles a SymbolTable from TSV file."""

import argparse
import json
import unicodedata

from typing import List

import pynini

def _char_processor(token: str, special: List[str]) -> List[str]:
    """Returns a list of characters with unseparated diacritics
    """
    chars = []
    for char in token:
        # Keep combining characters together
        if char in special:
            m = chars.pop(-1)
            chars.append(f"{m}{char}")
        else:
            chars.append(char)
    return chars
  
def main(args: argparse.Namespace) -> None:

    with open("combining.json", "r") as src:
        combining = json.load(src)

    syms = set()
    with open(args.input_lexicon, "r") as src:
        for line in src:
            normline = unicodedata.normalize("NFC", line.strip())
            ortho, phon = normline.split("\t")
            syms.update(_char_processor(ortho, combining))
            syms.update(_char_processor(phon, combining))

    sym = pynini.SymbolTable()
    key = 0
    sym.add_symbol(symbol="<eps>", key=key)
    for s in syms:
        key+=1
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



