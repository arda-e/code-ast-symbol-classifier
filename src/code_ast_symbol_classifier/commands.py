"""What each CLI command actually does.

Separate from argument parsing so a command can be called directly from a test
or a notebook without going through argv.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import explain as explain_module
from .config import REPORTS_DIR, TrainingConfig
from .data.dataset import LabeledDataset
from .data.loader import join, load_labelset, load_symbols
from .evaluation.report import render
from .experiments.ablation import run_ablation
from .experiments.table import render as render_table
from .features.spec import FeatureSpec
from .pipeline import cross_validate, train_final
from .taxonomy import Taxonomy


def load_dataset(symbols_path: Path, labels_path: Path, taxonomy: Taxonomy) -> LabeledDataset:
    dataset = join(load_symbols(symbols_path), load_labelset(labels_path), taxonomy)

    if dataset.orphan_labels:
        print(
            f"warning: {len(dataset.orphan_labels)} labels reference symbols missing from "
            f"{symbols_path.name}; the labels and the extraction may be from different revisions",
            file=sys.stderr,
        )
    return dataset


def inspect(spec: FeatureSpec, taxonomy: Taxonomy) -> int:
    """Print what the contracts currently declare.

    The first command worth running in a fresh clone: it works before any model
    exists and says what the project is currently committed to.
    """
    print(f"feature spec   : {spec.version}")
    print(
        f"  hash         : {spec.hash.algorithm}, "
        f"seed={spec.hash.seed}, buckets={spec.hash.buckets}"
    )
    print(f"  numeric      : {len(spec.numeric_fields)} fields")
    print(f"  vector size  : {spec.vector_size}")
    print(f"  variants     : {', '.join(sorted(spec.variants))}")
    print(f"taxonomy       : {taxonomy.version}, {len(taxonomy.classes)} classes")

    undefined = taxonomy.undefined_classes
    if undefined:
        print(
            f"\n  {len(undefined)} of {len(taxonomy.classes)} classes have no definition:\n"
            f"    {', '.join(undefined)}\n"
            "  Labelling against undefined classes produces disagreement that looks like\n"
            "  labeller error but is a missing definition. See docs/taxonomy.md."
        )
    return 0


def explain(
    symbols_path: Path,
    wanted: str | None,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    model_path: Path,
) -> int:
    records = load_symbols(symbols_path)
    record = explain_module.find_record(records, wanted)
    return explain_module.explain(
        record, records, spec=spec, taxonomy=taxonomy, model_path=model_path
    )


def evaluate(
    dataset: LabeledDataset,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    config: TrainingConfig,
) -> int:
    result = cross_validate(dataset, spec=spec, taxonomy=taxonomy, config=config)
    report = render(
        result,
        title=f"Evaluation — variant {config.variant}",
        context={
            "labelset": dataset.labelset_id,
            "taxonomy": dataset.taxonomy_version,
            "featureVersion": spec.version,
            "folds": config.folds,
            "seed": config.seed,
        },
    )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"evaluate-{config.variant}.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


def ablate(
    dataset: LabeledDataset,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    config: TrainingConfig,
    variants: tuple[str, ...],
) -> int:
    rows = run_ablation(dataset, spec=spec, taxonomy=taxonomy, config=config, variants=variants)
    table = render_table(rows)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "ablation.md").write_text(table + "\n", encoding="utf-8")
    print(table)
    return 0


def train(
    dataset: LabeledDataset,
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    config: TrainingConfig,
    out: Path,
) -> int:
    artifact = train_final(dataset, spec=spec, taxonomy=taxonomy, config=config)
    written = artifact.write(out)
    print(f"wrote {written} ({written.stat().st_size / 1024:.1f} KB)")
    return 0
