"""Model inputs: feature sets and the leakage guard (CLAUDE.md section 4; ADR-025, ADR-029).

Every feature must be known before ignition. ``check_pre_ignition`` raises if a feature list
contains a post-ignition quantity (list in fif.data.features.POST_IGNITION) or anything that is
not on the explicit allow-list below. Tests call it on every feature set.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fif.data.features import POST_IGNITION
from fif.physics.droplet import evaluate_flex

# Allow-list: raw pre-ignition conditions + physics computed only from them (fif.physics.droplet).
RAW_FEATURES = ["fuel_methanol", "ln_p_atm", "x_o2", "x_co2", "x_he", "ln_d0_mm"]
PHYSICS_FEATURES = ["ln_K_theory", "B", "T_f_kK", "Y_O2", "ln_alpha_g"]
EXTINCTION_PHYSICS = ["T_f_kK", "ln_chi_rad_proxy", "ln_tau_res_proxy", "flame_standoff"]
ALLOWED = set(RAW_FEATURES) | set(PHYSICS_FEATURES) | set(EXTINCTION_PHYSICS)

FEATURE_SETS = {
    # K (target ln K_meas)
    "K_pure_ml": RAW_FEATURES,
    "K_hybrid_residual": RAW_FEATURES + PHYSICS_FEATURES,
    # extinction yes/no
    "ext_physics": EXTINCTION_PHYSICS,
    "ext_pure_ml": RAW_FEATURES,
    "ext_hybrid": RAW_FEATURES + EXTINCTION_PHYSICS,
    # d_ext / d0
    "dext_pure_ml": RAW_FEATURES,
    "dext_hybrid": RAW_FEATURES + EXTINCTION_PHYSICS,
}

# Physical direction of P(extinction) used for monotonic constraints / sign checks (ADR-029):
# -1 = probability decreases with the feature, +1 = increases, 0 = free.
EXTINCTION_DIRECTIONS = {"x_o2": -1, "T_f_kK": -1, "x_co2": +1}


class LeakageError(ValueError):
    pass


def check_pre_ignition(features: list[str]) -> None:
    """Raise LeakageError if any feature is post-ignition or not on the allow-list."""
    post = [f for f in features if f in POST_IGNITION or any(f.startswith(p) for p in ("K_m2_s", "d_ext", "burn_time", "test_end", "extinct"))]
    unknown = [f for f in features if f not in ALLOWED]
    if post or unknown:
        raise LeakageError(f"post-ignition: {post}; not on allow-list: {unknown}")


def model_table(flex: pd.DataFrame) -> pd.DataFrame:
    """Processed FLEX rows used for modeling (use_in_model) + physics + model features + targets."""
    f = flex[flex["use_in_model"]].copy()
    f = pd.concat([f, evaluate_flex(f)], axis=1)
    f["ln_p_atm"] = np.log(f["p_atm"])
    f["ln_d0_mm"] = np.log(f["d0_m"] * 1e3)
    f["ln_K_theory"] = np.log(f["K_theory"])
    f["T_f_kK"] = f["T_f"] / 1000.0
    f["ln_alpha_g"] = np.log(f["alpha_g"])
    f["ln_chi_rad_proxy"] = np.log(f["chi_rad_proxy"])
    f["ln_tau_res_proxy"] = np.log(f["tau_res_proxy"])
    # targets (post-ignition; never in feature lists)
    f["y_lnK"] = np.log(f["K_m2_s"])
    f["y_ext"] = f["extinct_finite_d"]
    f["y_dext"] = f["d_ext_over_d0"]
    return f
