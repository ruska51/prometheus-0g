"""Helpers shared by the parsers: CSV decoding and literal number parsing.

Parsing rule: a cell becomes a float only if ``float(cell)`` succeeds on the stripped text.
Anything else (``""``, en dash ``"–"``, ``"~6"``, ``"#DIV/0!"``) becomes NaN and the original
text is kept in a ``*_raw`` column by the caller, so nothing is lost or silently changed.
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path


def read_csv_text(path: Path) -> tuple[str, list[list[str]]]:
    """Decode a PSI CSV (UTF-8 with BOM, else cp1252) and return (encoding, rows incl. header)."""
    raw = path.read_bytes()
    try:
        text, enc = raw.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        text, enc = raw.decode("cp1252"), "cp1252"
    rows = list(csv.reader(io.StringIO(text)))
    return enc, rows


def to_float(cell: str) -> float:
    """Literal float parse of a stripped cell; NaN if not a plain number."""
    try:
        return float(cell.strip())
    except ValueError:
        return math.nan
