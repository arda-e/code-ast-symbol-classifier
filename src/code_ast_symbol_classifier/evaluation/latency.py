"""Timing predictions.

Latency is on the reporting checklist for a reason that outlives this model: the
choice between a few hundred KB of weights and a 90 MB encoder is decided by cost
as much as by accuracy, and cost has to be a measurement rather than an estimate.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LatencyStats:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    cold_start_ms: float
    samples: int

    @staticmethod
    def measure(predict: Callable[[int], object], n: int, *, warmup: int = 20) -> LatencyStats:
        """Time `n` single predictions, reporting the first call separately.

        Cold start is taken before warmup because it is a real production cost:
        the first symbol after a process starts pays it.
        """
        if n < 1:
            raise ValueError("need at least one timed call")

        started = time.perf_counter()
        predict(0)
        cold_start_ms = (time.perf_counter() - started) * 1000

        for i in range(warmup):
            predict(i % n)

        timings = []
        for i in range(n):
            call_started = time.perf_counter()
            predict(i)
            timings.append((time.perf_counter() - call_started) * 1000)

        p50, p95, p99 = np.percentile(timings, [50, 95, 99])
        return LatencyStats(
            p50_ms=float(p50),
            p95_ms=float(p95),
            p99_ms=float(p99),
            cold_start_ms=cold_start_ms,
            samples=n,
        )
