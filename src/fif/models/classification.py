"""Classifiers for finite-diameter extinction (target y_ext, ADR-018, ADR-029).

- ``PriorModel``: training prevalence.
- ``logistic``: StandardScaler + L2 logistic regression, class_weight='balanced' (coefficients interpretable).
- ``boosting``: HistGradientBoostingClassifier, class_weight='balanced', optionally with monotonic
  constraints from fif.models.features.EXTINCTION_DIRECTIONS (ADR-029: run with and without).
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import EXTINCTION_DIRECTIONS
from .regression import SEED


class PriorModel:
    name = "prior"

    def fit(self, X, y):
        self.p = float(np.mean(y))
        return self

    def predict_proba(self, X):
        p = np.full(len(X), self.p)
        return np.column_stack([1 - p, p])


def logistic(C: float = 1.0):
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight="balanced", max_iter=5000))


def boosting(features: list[str], monotonic: bool, seed: int = SEED):
    cst = [EXTINCTION_DIRECTIONS.get(f, 0) for f in features] if monotonic else None
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=10,
                                          l2_regularization=1.0, class_weight="balanced",
                                          monotonic_cst=cst, random_state=seed)
