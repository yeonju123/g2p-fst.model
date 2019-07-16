#!/usr/bin/env python
"""makes the covering grammar of g and p"""


import argparse
import logging
import pynini
import pywrapfst as fst


def _create_container(g_far_path, p_far_path):
    g_far_reader = pynini.Far(g_far_path, mode="r")
    p_far_reader = pynini.Far(p_far_path, mode="r")
    g_container = set()
    p_container = set()
    while not g_far_reader.done():
        g_fsa = g_far_reader.get_fst()
        g_labels_extract = g_fsa.paths().ilabels()
        g_container.update(g_labels_extract)
        g_far_reader.next()
    while not p_far_reader.done():
        p_fsa = p_far_reader.get_fst()
        p_labels_extract = p_fsa.paths().ilabels()
        p_container.update(p_labels_extract)
        p_far_reader.next()
    g_far_reader.reset()
    p_far_reader.reset()
    return g_container, p_container


def _make_star(container: set[int]) -> pynini.Fst:
    lattice = pynini.Fst()
    starting_state = lattice.add_state()
    lattice.set_start(starting_state)
    lattice.set_final(starting_state)
    for label in container:
        lattice.add_arc(
            starting_state, pynini.Arc(label, label, None, starting_state)
        )
    assert lattice.verify()
    return lattice


def size(f):
    """Computes the number of arcs and states in the FST."""
    return sum(1 + f.num_arcs(state) for state in f.states())


def main(args):
    g_set, p_set = _create_container(args.g_far_path, args.p_far_path)
    g_lattice = _make_star(g_set)
    p_lattice = _make_star(p_set)
    logging.info("Sigma star is built. Now transducer is being constructed.")
    covering = pynini.transducer(g_lattice, p_lattice)
    fst_size = size(covering)
    if args.rmepsilon:
        covering.rmepsilon()
        logging.info("Epsilons are removed from the covering grammar")
    assert covering.verify()
    logging.info(
        "the number of arcs and states in the covering grammar is %d", fst_size
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--g_far_path", required=True, help="input grapheme FAR path"
    )
    parser.add_argument(
        "--p_far_path", required=True, help="input phoneme FAR path"
    )
    parser.add_argument(
        "--rmepsilon",
        default=True,
        help="removal of epsilon in the covering grammar. Default = True",
    )
    main(parser.parse_args())
