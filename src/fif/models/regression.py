"""Regression models for ln K (burning-rate constant) and d_ext/d0 (stage 5, ADR-029).

Four comparable models for K, all predicting ln K with a predictive standard deviation:
- ``MeanModel``      : training mean of ln K; sigma = training std.
- ``PhysicsModel``   : ln K_theory (Law & Williams, no fitting); sigma = training std of ln(K/K_theory).
- ``GPModel``        : Gaussian process on the given features predicting the target directly (pure ML).
- ``HybridKModel``   : ln K_theory + ln c_f(fuel) + GP(residual). c_f = exp(mean ln(K_meas/K_theory)) per fuel
                       on the training fold (docs/FORMULAS.md section 8); GP on r = ln(K_meas/(c_f K_theory)).
GP: StandardScaler + ConstantKernel x RBF (one length scale per feature) + WhiteKernel, normalize_y,
fixed random_state. Its predictive std grows away from the training data.
"""

from __future__ import annotations

from typing import Self

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20261114


def _gp(n_features: int, seed: int = SEED) -> Pipeline:
    kernel = ConstantKernel(1.0, (1e-3, 1e2)) * RBF(np.ones(n_features), (1e-2, 1e3)) + WhiteKernel(0.05, (1e-5, 1.0))
    return make_pipeline(
        StandardScaler(), GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=3, random_state=seed)
    )


class MeanModel:
    name = "mean"

    def fit(self, X: np.ndarray, y: np.ndarray, **_: object) -> Self:
        self.mu, self.sd = float(np.mean(y)), float(np.std(y, ddof=1))
        return self

    def predict(self, X: np.ndarray, **_: object) -> tuple[np.ndarray, np.ndarray]:
        n = len(X)
        return np.full(n, self.mu), np.full(n, self.sd)


class PhysicsModel:
    """Predicts the physics value itself (column ``ln_theory`` passed via ``aux``)."""

    name = "physics"

    def fit(self, X: np.ndarray, y: np.ndarray, aux: dict | None = None) -> Self:
        self.sd = float(np.std(y - aux["ln_theory"], ddof=1))
        return self

    def predict(self, X: np.ndarray, aux: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
        return np.asarray(aux["ln_theory"], dtype=float), np.full(len(X), self.sd)


class GPModel:
    name = "pure_ml_gp"

    def __init__(self, seed: int = SEED) -> None:
        self.seed = seed

    def fit(self, X: np.ndarray, y: np.ndarray, **_: object) -> Self:
        self.m = _gp(X.shape[1], self.seed).fit(X, y)
        return self

    def predict(self, X: np.ndarray, **_: object) -> tuple[np.ndarray, np.ndarray]:
        mu, sd = self.m.predict(X, return_std=True)
        return mu, sd


class HybridKModel:
    name = "hybrid"

    def __init__(self, seed: int = SEED) -> None:
        self.seed = seed

    def fit(self, X: np.ndarray, y: np.ndarray, aux: dict | None = None) -> Self:
        lt, fuel = np.asarray(aux["ln_theory"]), np.asarray(aux["fuel"])
        self.ln_cf = {f: float(np.mean((y - lt)[fuel == f])) for f in np.unique(fuel)}
        r = y - lt - np.array([self.ln_cf[f] for f in fuel])
        self.gp = _gp(X.shape[1], self.seed).fit(X, r)
        return self

    def predict(self, X: np.ndarray, aux: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
        lt, fuel = np.asarray(aux["ln_theory"]), np.asarray(aux["fuel"])
        r_mu, r_sd = self.gp.predict(X, return_std=True)
        # a fuel unseen in training (leave-fuel-out test) gets the mean calibration of the known fuels
        fallback = float(np.mean(list(self.ln_cf.values())))
        return lt + np.array([self.ln_cf.get(f, fallback) for f in fuel]) + r_mu, r_sd

    @property
    def c_f(self) -> dict[str, float]:
        return {f: float(np.exp(v)) for f, v in self.ln_cf.items()}
