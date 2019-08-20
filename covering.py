#!/usr/bin/env python
"""Constructs a covering grammar FST from the FARs produced by lexicon.py."""


import argparse
import logging

from typing import Set


import pynini


def _get_labels(far_path: str) -> Set[int]:
    """Collects all observed labels from an FSA."""
    labels: Set[int] = set()
    with pynini.Far(far_path, mode="r") as far_reader:
        while not far_reader.done():
            fsa = far_reader.get_fst()
            # Only looks at the input side, assuming an FSA.
            labels.update(fsa.paths().ilabels())
            far_reader.next()
    return labels


def _make_union(labels: Set[int], epsilon: bool) -> pynini.Fst:
    """Creates FSA over a union of the labels."""
    if epsilon:
        labels.add(0)
    lattice = pynini.Fst()
    src = lattice.add_state()
    lattice.set_start(src)
    dst = lattice.add_state()
    for label in labels:
        lattice.add_arc(src, pynini.Arc(label, label, None, dst))
    lattice.set_final(dst)
    assert lattice.verify(), "FST is ill-formed"
    return lattice


def _narcs(f: pynini.Fst) -> int:
    """Computes the number of arcs in an FST."""
    return sum(f.num_arcs(state) for state in f.states())


def main(args: argparse.Namespace) -> None:
    g_labels = _get_labels(args.g_far_path)
    logging.info("%d unique graphemes", len(g_labels))
    g_lattice = _make_union(g_labels, args.input_epsilon)
    p_labels = _get_labels(args.p_far_path)
    logging.info("%d unique phonemes", len(p_labels))
    p_lattice = _make_union(p_labels, args.output_epsilon)
    # The covering grammar is defined as the closure of the cross-product of
    # the input and output labels, corresponding to a Markov order-0 model.
    covering = pynini.transducer(g_lattice, p_lattice).closure().optimize()
    assert covering.num_states() == 1, "FST is ill-formed"
    logging.info("Covering grammar has %d arcs", _narcs(covering))
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
