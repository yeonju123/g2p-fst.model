#!/usr/bin/env python
""" make a language model from alignments.far produced by baumwelchdecode."""


import argparse
import logging
import os
import pynini
import subprocess
import typing


def main(args: argparse.Namespace) -> None:
    with pynini.Far(args.alignments_path, mode="r") as far_reader:
        encoder = pynini.EncodeMapper(
            far_reader.arc_type(), encode_labels=True
        )
        fst_key = 1
        with pynini.Far(
            "ngramdata.far",
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

        model_name = "model.lm"
        cmd = [
            "ngramcount",
            "--require_symbols=false",
            f"--order={args.ngram}",
            "ngramdata.far",
            "lm.cnt",
        ]
        subprocess.check_call(cmd)
        cmd1 = [
            "ngrammake",
            f"--method={args.smoothing}",
            "lm.cnt",
            model_name,
        ]
        subprocess.check_call(cmd1)
        logging.info(
            "%s-gram %s Language model is built", args.ngram, args.smoothing
        )
        if args.ngramshrink:
            cmd = [
                "ngramshrink",
                "--method-relative_entropy",
                "--target_number_of_ngrams=100000",
                "model.lm",
                "model.shrunk.lm",
            ]
            model_name = "model.shrunk.lm"
        with pynini.Far(model_name, mode="r") as far_fsa_reader:
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
    os.remove("ngramdata.far")
    os.remove("lm.cnt")
    os.remove("model.lm")
    os.remove("model.shrunk.lm")


# write a function to delete all the temporal files. -> delet lm.cnt. and if ngramshrink, delete model.lm

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
        "--smoothing", required=True, help="input smoothing method"
    )
    parser.add_argument(
        "--ngramshrink", default=False, help="make a compact ngram model"
    )
    main(parser.parse_args())
