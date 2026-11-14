"""Data-layer tests: row counts, schema, reference rows, flags, rebuild into a temp dir.

The pipeline is always built into pytest's tmp_path, never into data/ (live files untouched).
Reference values are copied from NASA/TP-2015-216046 Table IX (page numbers in comments).
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from fif.data import build, catalog, schema


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("data_build")
    res = build.build(out_root=out)
    res["out"] = out
    return res


def test_raw_checksums():
    assert catalog.verify() >= 72


def test_row_counts(built):
    assert len(built["flex"]) == 274
    assert len(built["cfig"]) == 333
    assert (built["cfig"]["table"] == "normal").sum() == 179
    assert len(built["catalog"]) == 24


def test_schemas_validate(built):
    schema.FLEX.validate(built["flex"])
    schema.CFIG.validate(built["cfig"])
    schema.CATALOG.validate(built["catalog"])


def test_provenance_columns(built):
    for name in ("flex", "cfig", "catalog"):
        df = built[name]
        for col in ("source_id", "source_file", "row_id", "quality_flag"):
            assert col in df.columns, (name, col)
    assert built["flex"]["row_id"].is_unique


def _row(df, ident, d0=None):
    sel = df[df["flex_identifier"] == ident]
    if d0 is not None:
        sel = sel[sel["d0_mm_orig"] == d0]
    assert len(sel) == 1
    return sel.iloc[0]


def test_reference_row_flex_001(built):
    # TP Table IX p. 20: FLEX-001 20CAL08, 757.7 mmHg, 0.21/0.79/0/0, d0 1.69, d_ext 0.89, K 0.52 mm2/s, 4.3 s, Disruption
    r = _row(built["flex"], "20CAL08")
    assert r.p_mmHg_orig == pytest.approx(757.7)
    assert r.p_Pa == pytest.approx(757.7 * 101325 / 760)
    assert (r.x_o2, r.x_n2, r.x_co2, r.x_he) == (0.21, 0.79, 0.0, 0.0)
    assert r.d0_m == pytest.approx(1.69e-3)
    assert r.d_ext_m == pytest.approx(0.89e-3)
    assert r.K_m2_s == pytest.approx(0.52e-6)
    assert r.burn_time_s == pytest.approx(4.3)
    assert r.test_end == "Disruption"
    assert r.extinct_finite_d == 1


def test_reference_row_c13h201_min_K(built):
    # TP p. 23: FLEX-130 C13H201 Heptane 537.2 mmHg, 0.17/0.38/0.45/0, d0 2.91, d_ext 2.89, K .05, 0.6 s
    r = _row(built["flex"], "C13H201")
    assert r.K_mm2_s_orig == pytest.approx(0.05)
    assert r.diluent == "CO2"
    assert r.d_ext_over_d0 == pytest.approx(2.89 / 2.91)


def test_zero_pressure_excluded_and_flagged(built):
    # TP p. 23: FLEX-114 C11M201 printed with ambient pressure 0
    r = _row(built["flex"], "C11M201")
    assert r.p_Pa == 0
    assert "P_NONPOSITIVE" in r.quality_flag
    assert not r.use_in_model
    assert built["flex"]["use_in_model"].sum() == 273


def test_extinction_class_counts(built):
    vc = built["flex"]["extinct_finite_d"].value_counts(dropna=False)
    assert vc.get(1) == 189 and vc.get(0) == 36
    assert built["flex"]["extinct_finite_d"].isna().sum() == 49


def test_targets_not_features(built):
    # leakage guard: post-ignition columns must never be listed as pre-ignition features
    from fif.data.features import PRE_IGNITION_FEATURES, POST_IGNITION
    assert not set(PRE_IGNITION_FEATURES) & set(POST_IGNITION)
    assert set(PRE_IGNITION_FEATURES) <= set(built["flex"].columns)


def test_cv_groups(built):
    g = built["flex"]["cv_group"]
    assert g.nunique() == 81
    # repeats of one regime share a group: all cabin-air methanol tests near 760 mmHg
    sel = built["flex"][(built["flex"]["fuel"] == "Methanol") & (built["flex"]["x_o2"] == 0.21)
                        & (built["flex"]["diluent"] == "N2") & (built["flex"]["p_mmHg_orig"].between(735, 785))]
    assert sel["cv_group"].nunique() == 1


def test_cfig_reference_and_flags(built):
    c = built["cfig"]
    first_inv = c[(c["table"] == "inverse") & (c["test_id"] == "21196 A1")].iloc[0]
    assert first_inv.hot_ignition == "no" and first_inv.ignited == 0
    assert first_inv.x_o2_oxidizer == pytest.approx(0.21)
    assert c["quality_flag"].str.contains("EXCEL_ERROR_TAD_K").sum() == 2
    assert math.isclose(c["x_o2_oxidizer"].max(), 0.85)


def test_rebuild_is_deterministic(built, tmp_path):
    res2 = build.build(out_root=tmp_path)
    a = pd.read_csv(built["out"] / "processed" / "flex.csv")
    b = pd.read_csv(tmp_path / "processed" / "flex.csv")
    pd.testing.assert_frame_equal(a, b)
