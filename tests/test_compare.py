"""Comparison matrix (S5, ADR-037): headers-derived ticks agree with what the raw tables contain."""
import pytest

from fif.insights.compare import VARIABLES, comparison_matrix, hardware_groups, table_headers


@pytest.fixture(scope="module")
def m():
    return comparison_matrix().set_index("acronym")


def test_all_24_investigations(m):
    assert len(m) == 24 and m["psi_id"].is_unique


def test_flex_records_conditions_and_outcomes(m):
    f = m.loc["FLEX"]
    for col in ("oxygen", "pressure", "inert / diluent", "sample / droplet size", "extinction outcome",
                "burning, spread or mass-loss rate / time"):
        assert f[col], col
    assert not f["air or gas flow"]  # FLEX: quiescent droplets, no flow column


def test_ambient_temperature_is_not_flame_temperature(m):
    col = "measured burner / flame temperature"
    assert not m.loc["FLEX-2"][col]  # header "Ambient Temperature (C)"
    assert not m.loc["ACME/Flame Design"][col]  # only computed Tad
    assert m.loc["ACME CFI-G"][col]  # "Peak burner T (C )"


def test_no_table_means_no_ticks(m):
    labels = [v[0] for v in VARIABLES]
    assert not m.loc[~m["has_table"], labels].to_numpy().any()
    assert table_headers(None) == [] and table_headers("") == []


def test_shared_hardware_families():
    g = hardware_groups()
    assert set(g["MDCA (droplet apparatus)"]) == {"FLEX", "FLEX-2", "CFI"}
    assert set(g["Saffire in Cygnus"]) == {"SAFFIRE-I", "SAFFIRE-II", "SAFFIRE-III"}
    assert all(len(v) >= 2 for v in g.values())
