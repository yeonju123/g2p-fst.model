#!/usr/bin/env python
"""Compiles FAR lexicons and covering grammar from TSV file."""


import argparse
import functools
import logging
import json

from typing import Set

import pynini
import pywrapfst


def _type_reader(_type: str) -> pynini.SymbolTable or str:
    """Allows for token_type from a SymbolTable text file
    """
    if _type not in ["byte", "utf8"]:
        assert pynini.SymbolTable.read_text(
            _type
        ), "type must be 'byte', 'utf8' or SymbolTable"
        _token_type = pynini.SymbolTable.read_text(_type)
    else:
        _token_type = _type
    return _token_type


def _text_processor(token: str) -> str:
    """Returns processed text with added whitespace between characters
    """
    with open("combining.json", "r") as src:
        combining = json.load(src)
    chars = []
    for char in token:
        # Keep combining characters together
        if char in combining:
            m = chars.pop(-1)
            chars.append(f"{m}{char}")
        else:
            chars.append(char)
    return " ".join(chars)


def _label_union(labels: Set[int], epsilon: bool) -> pynini.Fst:
    """Creates FSA over a union of the labels."""
    if epsilon:
        labels.add(0)
    side = pynini.Fst()
    src = side.add_state()
    side.set_start(src)
    dst = side.add_state()
    for label in labels:
        side.add_arc(src, pynini.Arc(label, label, None, dst))
    side.set_final(dst)
    assert side.verify(), "FST is ill-formed"
    return side


def _narcs(f: pynini.Fst) -> int:
    """Computes the number of arcs in an FST."""
    return sum(f.num_arcs(state) for state in f.states())


def main(args: argparse.Namespace) -> None:
    # Sets of labels for the covering grammar.
    g_labels: Set[int] = set()
    p_labels: Set[int] = set()
    # Curries compiler and compactor functions for the FARs.
    compiler = functools.partial(
        pynini.acceptor,
        token_type=_type_reader(args.token_type),
        attach_symbols=False,
    )
    compactor = functools.partial(pywrapfst.convert, fst_type="compact_string")
    logging.info("Constructing grapheme and phoneme FARs")
    g_writer = pywrapfst.FarWriter.create(args.g_far_path)
    p_writer = pywrapfst.FarWriter.create(args.p_far_path)
    with open(args.input_path, "r") as source:
        for (linenum, line) in enumerate(source, 1):
            key = f"{linenum:08x}"
            (g, p) = line.rstrip().split("\t", 1)
            if args.token_type not in ["byte", "utf8"]:
                _g = _text_processor(g)
                _p = _text_processor(p)
            else:
                _g = g
                _p = p
            # For both G and P, we compile a FSA, store the labels, and then
            # write the compact version to the FAR.
            g_fst = compiler(_g)
            g_labels.update(g_fst.paths().ilabels())
            g_writer[key] = compactor(g_fst)
            p_fst = compiler(_p)
            p_labels.update(p_fst.paths().ilabels())
            p_writer[key] = compactor(p_fst)
    logging.info("Processed %d examples", linenum)
    logging.info("Constructing covering grammar")
    logging.info("%d unique graphemes", len(g_labels))
    g_side = _label_union(g_labels, args.input_epsilon)
    logging.info("%d unique phonemes", len(p_labels))
    p_side = _label_union(p_labels, args.output_epsilon)
    # The covering grammar is given by (G x P)^*, a zeroth order Markov model.
    covering = pynini.transducer(g_side, p_side).closure().optimize()
    assert covering.num_states() == 1, "Covering grammar FST is ill-formed"
    logging.info("Covering grammar has %d arcs", _narcs(covering))
    covering.write(args.covering_path)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input_path", required=True, help="input TSV file path"
    )
    parser.add_argument(
        "--token_type",
        default="utf8",
        help="token type for acceptors. (default: %(default)s)",
    )
    parser.add_argument(
        "--g_far_path", required=True, help="output grapheme FAR path"
    )
    parser.add_argument(
        "--p_far_path", required=True, help="output phoneme FAR path"
    )
    parser.add_argument(
        "--input_epsilon",
        default=True,
        help="allows graphemes to have a null alignment (default: %(default)s)",
    )
    parser.add_argument(
        "--output_epsilon",
        default=True,
        help="allows phonemes to have a null alignment (default: %(default)s)",
    )
    parser.add_argument(
        "--covering_path", required=True, help="output covering FAR path"
    )
    main(parser.parse_args())
