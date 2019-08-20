#!/usr/bin/env python
""" make a language model from alignments.far produced by baumwelchdecode."""


import argparse
import logging
import os
import subprocess
import tempfile


import pynini


def main(args: argparse.Namespace) -> None:
    with pynini.Far(args.far_path, mode="r") as far_reader:
        encoder = pynini.EncodeMapper(
            far_reader.arc_type(), encode_labels=True
        )
        fsa_path = tempfile.mkstemp(text=True)[1]
        with pynini.Far(
            fsa_path,
            mode="w",
            arc_type=far_reader.arc_type(),
            far_type="default",
        ) as far_writer:
            while not far_reader.done():
                fst = far_reader.get_fst()
                assert fst.verify(), "FST is ill-formed"
                fst.encode(encoder)
                far_writer.add(far_reader.get_key(), fst)
                far_reader.next()
        count_path = tempfile.mkstemp(text=True)[1]
        lm_path = tempfile.mkstemp(text=True)[1]
        logging.info(
            "alignment.far is encoded to FSAs for training. Now training starts."
        )
        cmd = [
            "ngramcount",
            "--require_symbols=false",
            f"--order={args.order}",
            fsa_path,
            count_path,
        ]
        subprocess.check_call(cmd)
        os.remove(fsa_path)
        cmd1 = [
            "ngrammake",
            f"--method={args.smoothing_method}",
            count_path,
            lm_path,
        ]
        subprocess.check_call(cmd1)
        os.remove(count_path)
        if args.shrinking_method:
            shrunk_lm_sh = tempfile.mkstemp(text=True)[1]
            cmd = [
                "shrinking_method",
                "--method=relative_entropy",
                f"--target_number_of_ngrams={args.target_number_of_ngrams}",
                lm_path,
                shrunk_lm_sh,
            ]
            subprocess.check_call(cmd)
            lm_path = shrunk_lm_sh
        logging.info(
            "%s-gram %s Language model is trained.",
            args.order,
            args.smoothing_method,
        )
        # Decoding the LM
        model = pynini.Fst.read(lm_path)
        os.remove(lm_path)
        model.decode(encoder)
        model.write(args.model_path)

    logging.info(
        "%s-gram %s Language model is built.",
        args.order,
        args.smoothing_method,
    )


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level="INFO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--far_path", required=True, help="input alignments FAR path"
    )
    parser.add_argument(
        "--model_path", required=True, help="input result FST path"
    )
    parser.add_argument(
        "--order", required=True, help="input the order of ngram"
    )
    parser.add_argument(
        "--target_number_of_ngrams",
        default=100000,
        help="input the target number of ngrams (default: %(default)s)",
    )
    parser.add_argument(
        "--smoothing_method",
        default="kneser_ney",
        help="input smoothing method (default: %(default)s)",
    )
    parser.add_argument(
        "--shrinking_method",
        action="store_true",
        help="make a compact ngram model",
    )

    main(parser.parse_args())
