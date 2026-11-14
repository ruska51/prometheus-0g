"""Physicality tests on the saved interface models (stage 6, ADR-030).

Run after scripts/train_models.py. Checks: K rises with O2 (N2 balance) for both fuels, pressures and droplet
sizes; P(extinction) of the interface model does not rise with O2; K stays in a physical range; the GP
uncertainty grows outside the tested conditions; the reliability rule flags extrapolation.
"""
from __future__ import annotations

import joblib
import numpy as np
import pytest

from fif.data.catalog import REPO_ROOT
from fif.models.features import EXTINCTION_UI_MODEL, FEATURE_SETS, HYBRID_K_FEATURES, conditions_table
from fif.models.train import _aux
from fif.validation.reliability import SIGMA_UNRELIABLE, reliability

O2 = np.round(np.arange(0.12, 0.345, 0.01), 3)
CASES = [(f, p, d) for f in ("Methanol", "Heptane") for p in (0.7, 1.0) for d in (2.0, 3.5)]


@pytest.fixture(scope="module")
def models():
    k = joblib.load(REPO_ROOT / "models" / "K_hybrid.joblib")
    e = joblib.load(REPO_ROOT / "models" / f"ext_{EXTINCTION_UI_MODEL}.joblib")
    assert k["features"] == FEATURE_SETS[HYBRID_K_FEATURES]
    return k, e


@pytest.mark.parametrize("fuel,p,d0", CASES)
def test_K_increases_with_oxygen(models, fuel, p, d0):
    k, _ = models
    c = conditions_table(fuel, p, O2, d0_mm=d0)
    mu, _ = k["model"].predict(c[k["features"]].to_numpy(), aux=_aux(c))
    assert np.all(np.diff(np.exp(mu)) >= 0)


@pytest.mark.parametrize("fuel,p,d0", CASES)
def test_extinction_probability_does_not_rise_with_oxygen(models, fuel, p, d0):
    _, e = models
    c = conditions_table(fuel, p, O2, d0_mm=d0)
    pr = e["model"].predict_proba(c[e["features"]].to_numpy())[:, 1]
    assert np.all(np.diff(pr) <= 1e-12)


def test_K_in_physical_range_over_tested_box(models):
    k, _ = models
    c = conditions_table(np.array(["Methanol", "Heptane"])[:, None], np.array([0.7, 1.0, 2.0])[None, :], 0.21)
    mu, _ = k["model"].predict(c[k["features"]].to_numpy(), aux=_aux(c))
    K = np.exp(mu) * 1e6
    assert np.all((K > 0.1) & (K < 2.0))  # FLEX measured 0.05-1.06 mm2/s (one flagged outlier at 0.05)


def test_uncertainty_grows_outside_data(models):
    k, _ = models
    inside = conditions_table("Heptane", 1.0, 0.21, d0_mm=3.0)
    outside = conditions_table("Heptane", 1.0, 0.21, d0_mm=8.0)
    _, s_in = k["model"].predict(inside[k["features"]].to_numpy(), aux=_aux(inside))
    _, s_out = k["model"].predict(outside[k["features"]].to_numpy(), aux=_aux(outside))
    assert s_out[0] > 1.5 * s_in[0]


def test_reliability_rule():
    ok = reliability("Methanol", 1.0, 0.21, 0.0, 0.0, 3.0, sigma_log=0.11)
    assert ok["status"] == "in range"
    moon = reliability("Methanol", 10.2 / 14.696, 0.30, 0.0, 0.0, 3.0, sigma_log=0.13)
    assert moon["status"] == "extrapolation" and "pressure" in " ".join(moon["reasons"])
    wide = reliability("Heptane", 1.0, 0.21, 0.0, 0.0, 3.0, sigma_log=SIGMA_UNRELIABLE + 0.01)
    assert wide["status"] == "unreliable"
