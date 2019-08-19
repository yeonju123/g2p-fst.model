#!/usr/bin/env python
""" make a language model from alignments.far produced by baumwelchdecode."""


import argparse
import logging
import os
import pynini
import subprocess
import tempfile
import typing


def main(args: argparse.Namespace) -> None:
    with pynini.Far(args.alignments_path, mode="r") as far_reader:
        encoder = pynini.EncodeMapper(
            far_reader.arc_type(), encode_labels=True
        )
        fst_key = 1
        _, tmppath_ngram = tempfile.mkstemp(text=True)
        with pynini.Far(
            tmppath_ngram,
            mode="w",
            arc_type=far_reader.arc_type(),
            far_type="default",
        ) as far_writer:
            while not far_reader.done():
                key = f"{fst_key:08x}"
                fst = far_reader.get_fst()
                fst.encode(encoder)
                far_writer.add(key, fst)
                assert fst.verify(), "FST is ill-formed"
                far_reader.next()
                fst_key += 1
        _, tmppath_cnt = tempfile.mkstemp(text=True)
        _, tmppath_lm = tempfile.mkstemp(text=True)
        logging.info(
            "alignment.far is encoded to FSAs for training. Now training starts."
        )
        cmd = [
            "ngramcount",
            "--require_symbols=false",
            f"--order={args.ngram}",
            tmppath_ngram,
            tmppath_cnt,
        ]
        subprocess.check_call(cmd)
        cmd = [
            "ngrammake",
            f"--method={args.smoothing}",
            tmppath_cnt,
            tmppath_lm,
        ]
        subprocess.check_call(cmd)
        if args.ngramshrink:
            _, tmppath_lm_sh = tempfile.mkstemp(text=True)
            cmd = [
                "ngramshrink",
                "--method=relative_entropy",
                "--target_number_of_ngrams=100000",
                tmppath_lm,
                tmppath_lm_sh,
            ]
            subprocess.check_call(cmd)
            tmppath_lm = tmppath_lm_sh
        logging.info(
            "%s-gram %s Language model is trained.", args.ngram, args.smoothing
        )
        with pynini.Far(tmppath_lm, mode="r") as far_fsa_reader:
            fst_key = 1
            with pynini.Far(
                args.output_path,
                mode="w",
                arc_type=far_fsa_reader.arc_type(),
                far_type="default",
            ) as far_writer:
                while not far_fsa_reader.done():
                    key = f"{fst_key:08x}"
                    fst = far_fsa_reader.get_fst()
                    assert fst.verify(), "FST is ill-formed"
                    fst.decode(encoder)
                    far_writer.add(key, fst)
                    far_fsa_reader.next()
                    fst_key += 1
    os.remove(tmppath_ngram)
    os.remove(tmppath_cnt)
    os.remove(tmppath_lm)
    logging.info(
        "%s-gram %s Language model is built.", args.ngram, args.smoothing
    )


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--alignments_path", required=True, help="input alignments FAR path"
    )
    parser.add_argument(
        "--output_path", required=True, help="input result FST path"
    )
    parser.add_argument(
        "--ngram", required=True, help="input the order of ngram"
    )
    parser.add_argument(
        "--smoothing",
        default="kneser_ney",
        help="input smoothing method (default: %(default)s)",
    )
    parser.add_argument(
        "--ngramshrink", action="store_true", help="make a compact ngram model"
    )
    main(parser.parse_args())
