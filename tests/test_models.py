"""Model-layer tests: leakage guard, feature availability, hybrid mechanics, monotonic constraints.

Fast: no full cross-validation here (scripts/train_models.py does that, ~45 s).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fif.data.features import POST_IGNITION
from fif.models import classification as C
from fif.models import regression as R
from fif.models.features import (EXTINCTION_DIRECTIONS, FEATURE_SETS, LeakageError, check_pre_ignition,
                                 model_table)
from fif.data.catalog import REPO_ROOT


@pytest.fixture(scope="module")
def table():
    return model_table(pd.read_csv(REPO_ROOT / "data" / "processed" / "flex.csv"))


@pytest.mark.parametrize("name", sorted(FEATURE_SETS))
def test_every_feature_set_is_pre_ignition(name):
    check_pre_ignition(FEATURE_SETS[name])


@pytest.mark.parametrize("post", sorted(set(POST_IGNITION) | {"y_lnK", "y_ext", "y_dext", "burn_time_s"}))
def test_leakage_guard_rejects_post_ignition_columns(post):
    with pytest.raises(LeakageError):
        check_pre_ignition(FEATURE_SETS["K_hybrid_residual"] + [post])


def test_feature_columns_exist_and_targets_are_separate(table):
    for fs in FEATURE_SETS.values():
        assert set(fs) <= set(table.columns)
        assert not {"y_lnK", "y_ext", "y_dext"} & set(fs)


def test_hybrid_recovers_calibration_constant_on_synthetic_data():
    rng = np.random.default_rng(0)
    n = 120
    X = rng.normal(size=(n, 2))
    lt = rng.normal(-14, 0.3, n)
    fuel = np.where(rng.random(n) < 0.5, "A", "B")
    y = lt + np.where(fuel == "A", np.log(0.7), np.log(1.0)) + 0.1 * X[:, 0] + rng.normal(0, 0.02, n)
    m = R.HybridKModel().fit(X, y, aux={"ln_theory": lt, "fuel": fuel})
    assert m.c_f["A"] == pytest.approx(0.7, rel=0.05)
    mu, sd = m.predict(X, aux={"ln_theory": lt, "fuel": fuel})
    assert np.sqrt(np.mean((mu - y) ** 2)) < 0.05 and np.all(sd > 0)


def test_gp_uncertainty_grows_away_from_data():
    rng = np.random.default_rng(1)
    X = rng.uniform(0, 1, size=(60, 1)); y = np.sin(3 * X[:, 0]) + rng.normal(0, 0.05, 60)
    m = R.GPModel().fit(X, y)
    _, sd_in = m.predict(np.array([[0.5]]))
    _, sd_out = m.predict(np.array([[3.0]]))
    assert sd_out[0] > 2 * sd_in[0]


def test_monotonic_boosting_respects_direction():
    feats = ["x_o2", "x_he"]
    rng = np.random.default_rng(2)
    X = rng.uniform(0, 1, size=(300, 2))
    y = (rng.random(300) < 0.5).astype(int)  # pure noise: constraint must still hold
    m = C.boosting(feats, monotonic=True).fit(X, y)
    grid = np.column_stack([np.linspace(0, 1, 20), np.full(20, 0.5)])
    p = m.predict_proba(grid)[:, 1]
    assert EXTINCTION_DIRECTIONS["x_o2"] == -1
    assert np.all(np.diff(p) <= 1e-12)
