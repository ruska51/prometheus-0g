"""Leakage control: which processed FLEX columns are known before ignition (allowed features)
and which are measured after ignition (targets / analysis only). CLAUDE.md section 4.

``d0_m`` is allowed: NASA/TP-2015-216046 App. A.1 defines it as the droplet diameter at time
zero, when the igniters are turned on.
"""
from __future__ import annotations

PRE_IGNITION_FEATURES = [
    "fuel_methanol",  # fuel identity
    "p_Pa", "p_atm",  # ambient pressure
    "x_o2", "x_n2", "x_co2", "x_he", "x_inert",  # initial ambient composition
    "p_o2_Pa",  # O2 partial pressure = x_o2 * p
    "diluent",  # N2 / CO2 / He class
    "d0_m",  # initial droplet diameter at igniter ON
]

POST_IGNITION = [
    "K_m2_s", "K_mm2_s_orig",  # burning-rate constant
    "d_ext_m", "d_ext_mm", "d_ext_mm_orig", "d_ext_over_d0",  # extinction diameter
    "burn_time_s",
    "test_end",
    "extinct_finite_d",
]

TARGETS = {
    "K_m2_s": "burning-rate constant from d^2(t) fit (ADR-017)",
    "extinct_finite_d": "visible flame extinguished at finite droplet diameter (ADR-018)",
    "d_ext_over_d0": "relative extinction diameter (ADR-017)",
}

# Physics-derived features (ADR-025), computed by fif.physics.droplet.evaluate_flex from pre-ignition inputs only.
PHYSICS_FEATURES_K = ["ln_K_theory", "B", "T_f", "Y_O2", "alpha_g"]
PHYSICS_FEATURES_EXTINCTION = PHYSICS_FEATURES_K + ["d0_m", "chi_rad_proxy"]
