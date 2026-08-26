"""Walk one symbol through the pipeline and print every stage.

The pipeline is easy to describe and hard to picture. This command makes it
concrete: one real symbol, each stage shown as it happens, with the stages that
are not written yet naming themselves and pointing at their specification.

It stays useful the whole way through. On a fresh clone it prints the shape of
the work; as each stage is implemented, that section fills in with real output.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import GOLDEN_DIR
from .data.records import SymbolRecord
from .features.build import FeatureBuilder
from .features.hashing import hash_bucket
from .features.lexical import lexical_features
from .features.numeric import numeric_vector
from .features.spec import FeatureSpec
from .model import artifact as artifact_module
from .taxonomy import Taxonomy

RULE = "─" * 78


@dataclass(frozen=True)
class Attempt:
    """The result of calling a stage that may not be written yet."""

    value: Any = None
    missing: str | None = None

    @property
    def ok(self) -> bool:
        return self.missing is None


def attempt(call: Callable[[], Any]) -> Attempt:
    try:
        return Attempt(value=call())
    except NotImplementedError as exc:
        return Attempt(missing=str(exc))


def explain(
    record: SymbolRecord,
    corpus: list[SymbolRecord],
    *,
    spec: FeatureSpec,
    taxonomy: Taxonomy,
    model_path: Path | None = None,
) -> int:
    _symbol(record)

    lexical = attempt(lambda: lexical_features(record, spec))
    _stage_lexical(record, spec, lexical)

    numeric = attempt(lambda: numeric_vector(record, spec.numeric_fields))
    _stage_numeric(record, spec, numeric)

    # Fitted on the whole corpus, then asked for this one symbol. Fitting on the
    # single record would make the scaler treat its own values as the average and
    # standardise the entire numeric block to zero — technically correct, and a
    # misleading thing to show.
    vector = attempt(lambda: FeatureBuilder(spec=spec, variant="C").fit(corpus).transform([record]))
    _stage_vector(spec, vector)
    _stage_prediction(vector, taxonomy, model_path)
    return 0


def _symbol(record: SymbolRecord) -> None:
    print(f"\n{RULE}\n  SYMBOL\n{RULE}")
    print(f"  id       {record.id}")
    print(f"  name     {record.name}    owner: {record.owner or '—'}    kind: {record.kind}")
    print(f"  file     {record.file_path}")
    print(f"  calls    {', '.join(record.callees) if record.callees else '—'}")
    print(
        f"  types    accepts {', '.join(record.param_types) or '—'} -> {record.return_type or '—'}"
    )
    print(
        "\n  What the model does NOT get: the function body. No statements, no\n"
        "  comments, no variable names. Callee names are the only thing taken from\n"
        "  inside it, and they arrive already reduced to names."
    )


def _stage_lexical(record: SymbolRecord, spec: FeatureSpec, lexical: Attempt) -> None:
    print(f"\n{RULE}")
    print("  STAGES 1-2   names -> feature strings -> buckets   [features/lexical.py]")
    print(RULE)

    if not lexical.ok:
        print(f"  Not written yet: {lexical.missing}")
        print("  Specification:   tests/spec/test_stage1_split.py, then test_stage2_lexical.py")
        print(f"\n  The contract asks for {len(spec.namespaces)} sources of words:")
        print(f"    {', '.join(spec.namespaces)}")
        _golden_hint(record)
        return

    features: list[str] = sorted(lexical.value)
    for namespace in spec.namespaces:
        tokens = [f.split(":", 1)[1] for f in features if f.startswith(f"{namespace}:")]
        if tokens:
            print(f"  {namespace:<9} {', '.join(tokens)}")

    print(f"\n  {len(features)} feature strings -> buckets in a {spec.hash.buckets}-wide space:")
    for feature in features[:6]:
        print(f"    {feature:<24} -> {hash_bucket(feature, spec.hash):>5}")
    if len(features) > 6:
        print(f"    ... and {len(features) - 6} more")

    buckets = {hash_bucket(f, spec.hash) for f in features}
    if len(buckets) < len(features):
        print(
            f"\n  Note: {len(features)} strings landed in {len(buckets)} buckets — two of them\n"
            "  collided. Unavoidable when mapping unbounded strings into a fixed space,\n"
            "  and tolerable because each symbol only lights up a handful of positions."
        )


def _stage_numeric(record: SymbolRecord, spec: FeatureSpec, numeric: Attempt) -> None:
    print(f"\n{RULE}\n  STAGE 3   facts -> fixed-order block   [features/numeric.py]\n{RULE}")

    if not numeric.ok:
        print(f"  Not written yet: {numeric.missing}")
        print("  Specification:   tests/spec/test_stage3_numeric.py")
        print(
            f"\n  The contract reserves {len(spec.numeric_fields)} positions. This record carries "
            f"{len(record.numeric)} facts,\n  which have to be read out in the contract's order, "
            "not the record's:"
        )
        for name, value in list(record.numeric.items())[:6]:
            print(f"    {name:<26} {value:g}")
        if len(record.numeric) > 6:
            print(f"    ... and {len(record.numeric) - 6} more")
        return

    values = numeric.value
    print(f"  {len(values)} positions, {sum(1 for v in values if v)} of them non-zero:")
    for position, (field, value) in enumerate(zip(spec.numeric_fields, values, strict=True)):
        if value:
            print(f"    [{position:>2}] {field.name:<26} {value:g}   ({field.group})")


def _stage_vector(spec: FeatureSpec, vector: Attempt) -> None:
    print(f"\n{RULE}\n  STAGE 4   one vector   [features/build.py]\n{RULE}")

    if not vector.ok:
        print(f"  Not written yet: {vector.missing}")
        print("  Specification:   tests/spec/test_stage4_build.py")
        print(
            f"\n  Target shape: {spec.hash.buckets} buckets + {len(spec.numeric_fields)} numbers "
            f"= {spec.vector_size} positions."
        )
        return

    matrix = vector.value
    print(f"  shape {matrix.shape[1]} positions, {matrix.nnz} of them non-zero (a sparse vector)")
    zeros = matrix.shape[1] - matrix.nnz
    print(
        f"\n  Almost every position is zero — {zeros} of them here — so only the\n"
        "  non-zero ones are stored. That is what 'sparse' means.\n"
        "\n  The numeric half is standardised against the rest of the corpus, so its\n"
        "  values now read as 'how unusual is this symbol', not as raw counts."
    )


def _stage_prediction(vector: Attempt, taxonomy: Taxonomy, model_path: Path | None) -> None:
    print(f"\n{RULE}\n  STAGE 5   vector -> probabilities   [model/train.py]\n{RULE}")

    if not vector.ok:
        print("  Waiting on the stages above.")
        return

    if model_path is None or not model_path.exists():
        print(f"  No trained model at {model_path or 'models/model.v1.json'}.")
        print("  Run `make train` once stage 5 passes.")
        return

    artifact = artifact_module.read(model_path)
    probabilities = artifact.predict_proba(vector.value.toarray()[0])
    ranked = sorted(zip(artifact.classes, probabilities, strict=True), key=lambda p: -p[1])

    for label, probability in ranked[:4]:
        bar = "█" * round(probability * 30)
        print(f"    {label:<16} {probability:.3f}  {bar}")

    top_label, top_probability = ranked[0]
    if top_probability >= taxonomy.accept_threshold:
        verdict = f"accept — {top_label}"
    elif top_probability >= taxonomy.tentative_threshold:
        verdict = f"tentative — {top_label}, worth a human glance"
    else:
        verdict = "unknown — the prediction is thrown away"

    print(f"\n  {verdict}")
    print(
        "\n  The spread matters as much as the winner. A confident 0.94 and a coin-flip\n"
        "  0.45 both report the same top class, and only one of them means anything."
    )


def _golden_hint(record: SymbolRecord) -> None:
    """If this is the worked example, say what the contract expects for it."""
    golden_path = GOLDEN_DIR / "vector-golden.json"
    if not golden_path.exists():
        return

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    if golden["record"]["id"] != record.id:
        return

    expected = golden["expectedLexicalFeatures"]
    print(
        f"\n  This symbol is the worked example. The contract expects exactly "
        f"{len(expected)} strings\n  from it, listed in contracts/fixtures/vector-golden.json:"
    )
    print(f"    {', '.join(expected[:5])}, ...")


def find_record(records: list[SymbolRecord], wanted: str | None) -> SymbolRecord:
    """Pick a symbol by id, or by a fragment of its name."""
    if wanted is None:
        return records[0]

    for record in records:
        if record.id == wanted:
            return record

    matches = [record for record in records if wanted.lower() in record.name.lower()]
    if not matches:
        raise SystemExit(f"no symbol matching {wanted!r}; try one of: {records[0].name}, ...")
    return matches[0]
