#!/usr/bin/env python
"""Constructs a covering grammar FST from the FARs produced by lexicon.py."""


import argparse
import logging

from typing import Set


import pynini


def _get_labels(far_path: str) -> Set[int]:
    labels: Set[int] = set()
    with pynini.Far(far_path, mode="r") as far_reader:
        while not far_reader.done():
            fsa = far_reader.get_fst()
            label_extract = fsa.paths().ilabels()
            labels.update(label_extract)
            far_reader.next()
    return labels


def _make_star(labels: Set[int], epsilon: bool) -> pynini.Fst:
    lattice = pynini.Fst()
    starting_state = lattice.add_state()
    lattice.set_start(starting_state)
    lattice.set_final(starting_state)
    if epsilon:
        lattice.add_arc(starting_state, pynini.Arc(0, 0, None, starting_state))
    for label in labels:
        lattice.add_arc(
            starting_state, pynini.Arc(label, label, None, starting_state)
        )
    assert lattice.verify(), "FST is ill-formed"
    return lattice


def size(f: pynini.Fst) -> int:
    """Computes the number of arcs and states in the FST."""
    return sum(1 + f.num_arcs(state) for state in f.states())


def main(args: argparse.Namespace) -> None:
    g_labels = _get_labels(args.g_far_path)
    p_labels = _get_labels(args.p_far_path)
    g_lattice = _make_star(g_labels, args.input_epsilon)
    p_lattice = _make_star(p_labels, args.output_epsilon)
    covering = pynini.transducer(g_lattice, p_lattice)
    assert covering.verify(), "FST is ill-formed"
    fst_size = size(covering)
    logging.info("%d states and arcs", fst_size)
    covering.write(args.covering_path)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--g_far_path", required=True, help="input grapheme FAR path"
    )
    parser.add_argument(
        "--p_far_path", required=True, help="input phoneme FAR path"
    )
    parser.add_argument(
        "--input_epsilon",
        default=True,
        help="allows input graphemes to have a null alignment (default: %(default)s)",
    )
    parser.add_argument(
        "--output_epsilon",
        default=True,
        help="allows input phonemes to have a null alignment (default: %(default)s)",
    )
    parser.add_argument(
        "--covering_path", required=True, help="output covering FAR path"
    )
    main(parser.parse_args())
