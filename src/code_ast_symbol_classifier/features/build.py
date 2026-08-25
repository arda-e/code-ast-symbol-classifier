"""Assembling the final vector.  [UNIMPLEMENTED SLOT]

The two blocks are concatenated, not merged:

    [0,0,...,1,...,1,...,0]  +  [4, 4, 3, 1, 1, 1, 4, 0, 0, 0]
    └──── buckets (0/1) ───┘     └───── numeric, scaled ─────┘

Scaling applies to the numeric block only. Without it a single `inDegree = 47`
speaks out of all proportion next to 4096 zeros and ones, and can drown the rest.
The scaler is fitted on the training fold and reused on the test fold — fitting
it on everything leaks test data into training and inflates the score.

`FeatureBuilder` is stateful for exactly that reason: `fit` learns the scaler,
`transform` applies it, and the fitted parameters ship inside the model artifact
so inference can repeat the same transform.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy.sparse import csr_matrix

from ..data.records import SymbolRecord
from .spec import FeatureSpec


@dataclass
class FeatureBuilder:
    """Builds vectors for one ablation variant.

    Variants decide which blocks participate: `A` is lexical only, `B-local` is
    the file-local numeric groups, `B-global` the graph-global ones, `C` is
    everything. A disabled block contributes no columns at all.
    """

    spec: FeatureSpec
    variant: str = "C"

    def fit(self, records: list[SymbolRecord]) -> FeatureBuilder:
        """Fit the numeric scaler on these records. Returns self."""
        raise NotImplementedError("see contracts/feature-spec.v1.json -> numeric.scaling")

    def transform(self, records: list[SymbolRecord]) -> csr_matrix:
        """Vectorise records with the already-fitted scaler."""
        raise NotImplementedError("see contracts/feature-spec.v1.json -> ablationVariants")

    def fit_transform(self, records: list[SymbolRecord]) -> csr_matrix:
        return self.fit(records).transform(records)

    @property
    def scaler_params(self) -> tuple[list[float], list[float]] | None:
        """(mean, scale) for the numeric block, or None when it has no columns."""
        raise NotImplementedError("see contracts/model-artifact.md -> scaler")
