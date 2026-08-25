"""Paths and knobs, resolved in one place.

Anything a run depends on and a reader might want to reproduce belongs here, so
a report can name the settings that produced it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONTRACTS_DIR = Path(os.environ.get("CASC_CONTRACTS_DIR", PROJECT_ROOT / "contracts"))
FEATURE_SPEC_PATH = CONTRACTS_DIR / "feature-spec.v1.json"
TAXONOMY_PATH = CONTRACTS_DIR / "taxonomy.v1.yaml"
GOLDEN_DIR = CONTRACTS_DIR / "fixtures"

DATA_DIR = PROJECT_ROOT / "data"
FIXTURES_DIR = DATA_DIR / "fixtures"
LABELS_DIR = DATA_DIR / "labels"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"


@dataclass(frozen=True)
class TrainingConfig:
    """Settings the model artifact records, so a result can be reproduced.

    `C` is the regularisation strength and matters more than it looks: with a few
    hundred labelled examples against 4096+ features, an unconstrained model can
    memorise a private feature for every example, score perfectly in training and
    collapse on an unseen symbol. Smaller C means a simpler model.
    """

    variant: str = "C"
    regularisation: float = 0.5
    class_weight: str = "balanced"
    max_iter: int = 1000
    seed: int = 42
    folds: int = 5
