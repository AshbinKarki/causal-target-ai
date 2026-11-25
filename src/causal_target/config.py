"""Validated configuration and portable artifact locations."""

from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path

import yaml

FEATURES = [f"f{i}" for i in range(12)]
LABELS = ["treatment", "conversion", "visit", "exposure"]


@dataclass(frozen=True)
class Config:
    profile: str = "quick"
    sample_rows: int | None = 20000
    seed: int = 42
    trees: int = 60
    optuna_trials: int = 2
    bootstrap_reps: int = 150
    crossfit_folds: int = 3
    threads: int = 4
    causal_forest: bool = False
    forest_rows: int = 20000
    assignment_probability: float | None = None
    budget: float = 250
    intervention_cost: float = 0.05
    conversion_value: float = 50
    capacity_fraction: float = 0.3

    def __post_init__(self):
        if not all(
            isfinite(v)
            for v in [
                self.budget,
                self.intervention_cost,
                self.conversion_value,
                self.capacity_fraction,
            ]
        ):
            raise ValueError("Financial inputs must be finite")
        counts = [
            self.seed,
            self.trees,
            self.optuna_trials,
            self.bootstrap_reps,
            self.crossfit_folds,
            self.threads,
            self.forest_rows,
        ]
        if self.sample_rows is not None:
            counts.append(self.sample_rows)
        if any(not isinstance(v, int) or isinstance(v, bool) for v in counts):
            raise ValueError("Counts and seed must be integers")
        if self.seed < 0:
            raise ValueError("Seed must be nonnegative")
        if self.profile not in {"quick", "demo", "full"}:
            raise ValueError("profile must be quick, demo or full")
        if self.sample_rows is not None and self.sample_rows < 100:
            raise ValueError("sample_rows must be at least 100")
        if min(self.trees, self.bootstrap_reps, self.threads, self.forest_rows) < 1:
            raise ValueError("counts must be positive")
        if self.crossfit_folds < 2 or self.optuna_trials < 0:
            raise ValueError("invalid training configuration")
        if self.assignment_probability is not None and not 0 < self.assignment_probability < 1:
            raise ValueError("assignment_probability must be strictly between zero and one")
        if not 0 <= self.capacity_fraction <= 1:
            raise ValueError("capacity_fraction must lie in [0, 1]")
        if self.budget < 0 or self.intervention_cost <= 0 or self.conversion_value < 0:
            raise ValueError("invalid financial assumptions")

    @classmethod
    def read(cls, path: str | Path):
        return cls(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    def to_dict(self):
        return asdict(self)
