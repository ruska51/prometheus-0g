"""Smoke test: the project package imports. Stage: 0."""


def test_package_imports():
    import fif  # noqa: F401


def test_raw_data_unchanged():
    """Every raw file registered in data/catalog.yaml matches its sha256 (CLAUDE.md: data/raw is never modified)."""
    from fif.data.catalog import verify

    assert verify() >= 90
