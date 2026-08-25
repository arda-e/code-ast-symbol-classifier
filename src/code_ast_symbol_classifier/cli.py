"""Argument parsing and dispatch. The work itself lives in `commands.py`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import commands
from .config import FIXTURES_DIR, MODELS_DIR, TrainingConfig
from .experiments.ablation import DEFAULT_VARIANTS
from .features.spec import load_feature_spec
from .taxonomy import load_taxonomy

DATA_COMMANDS = {
    "evaluate": "cross-validate and write a full report",
    "train": "fit on all labels and write a model artifact",
    "ablate": "compare feature sets A / B-local / B-global / C",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code-ast-symbol-classifier")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect", help="show what the contracts currently declare")

    for name, help_text in DATA_COMMANDS.items():
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("--symbols", type=Path, default=FIXTURES_DIR / "symbols.sample.jsonl")
        sub.add_argument("--labels", type=Path, default=FIXTURES_DIR / "labels.sample.json")
        sub.add_argument("--variant", default="C")
        sub.add_argument("--folds", type=int, default=5)
        sub.add_argument("--seed", type=int, default=42)

        if name == "ablate":
            sub.add_argument("--variants", default=",".join(DEFAULT_VARIANTS))
        if name == "train":
            sub.add_argument("--out", type=Path, default=MODELS_DIR / "model.v1.json")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args)
    except NotImplementedError as exc:
        # A fresh clone hits this on the first `evaluate`. A stack trace would
        # read as a broken repository; it is a slot nobody has filled yet.
        print(
            f"\nThis command needs a module that is not written yet: {exc}\n"
            "Run `make spec` to see the failing specifications — they are the to-do list.",
            file=sys.stderr,
        )
        return 2


def _dispatch(args: argparse.Namespace) -> int:
    spec = load_feature_spec()
    taxonomy = load_taxonomy()

    if args.command == "inspect":
        return commands.inspect(spec, taxonomy)

    dataset = commands.load_dataset(args.symbols, args.labels, taxonomy)
    config = TrainingConfig(variant=args.variant, folds=args.folds, seed=args.seed)

    if args.command == "evaluate":
        return commands.evaluate(dataset, spec=spec, taxonomy=taxonomy, config=config)

    if args.command == "ablate":
        variants = tuple(name.strip() for name in args.variants.split(",") if name.strip())
        return commands.ablate(
            dataset, spec=spec, taxonomy=taxonomy, config=config, variants=variants
        )

    return commands.train(dataset, spec=spec, taxonomy=taxonomy, config=config, out=args.out)


if __name__ == "__main__":
    raise SystemExit(main())
