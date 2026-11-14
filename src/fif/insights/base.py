"""Insight object, evidence weights and ranking formulas (stage 7, ADR-033).

Every number in an insight's text is computed when the insight function runs (no hard-coded numbers in
the text). Evidence types follow CLAUDE.md section 4.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

# Evidence-type weights: docs/FORMULAS.md section 8 (Ruslan's default).
EVIDENCE_WEIGHTS = {
    "NASA data": 1.0,
    "model": 0.7,
    "NASA literature": 0.6,
    "physics theory": 0.5,
    "NASA history": 0.5,
    "NASA spinoff": 0.3,
}
STAGES = ("prevention", "detection", "suppression")


@dataclass
class Insight:
    id: str
    stage: str  # prevention / detection / suppression / history / earth
    title: str
    finding: str
    action: str
    evidence_type: str
    n_tests: int
    effect: dict  # {"name", "value", "ci": [lo, hi] or None, "unit", "log_effect"}
    sources: list
    confidence: str  # high / medium / low
    extrapolation: bool = False
    related: list = field(default_factory=list)  # ids of linked insights (history <-> data)
    score: float = 0.0
    ru: dict = field(default_factory=dict)  # Russian title / finding / action (interface language switch)

    def to_dict(self) -> dict:
        return asdict(self)


def effect_strength(ins: Insight, scale: float = 0.5) -> float:
    """e in [0, 1]: |ln effect| / scale, capped at 1 (a factor exp(0.5) = 1.65 counts as full strength)."""
    le = ins.effect.get("log_effect")
    if le is None or (isinstance(le, float) and math.isnan(le)):
        return 0.0
    return min(abs(le) / scale, 1.0)


def score_evidence_log_n(ins: Insight) -> float:
    """Option A (FORMULAS.md section 8): S = w_type * ln(1 + n) * (0.3 + 0.7 e)."""
    return EVIDENCE_WEIGHTS[ins.evidence_type] * math.log1p(ins.n_tests) * (0.3 + 0.7 * effect_strength(ins))


def score_multicriteria(ins: Insight) -> float:
    """Option B: 0.4 evidence strength + 0.3 practical relevance + 0.3 effect strength, each in [0, 1].
    Evidence strength = w_type x (1 if the CI excludes 'no effect' else 0.5); relevance = 1 for insights tied to
    habitat atmosphere / detection / suppression decisions, 0.5 otherwise (field `related` non-empty or stage)."""
    ci = ins.effect.get("ci")
    sig = 1.0 if ci and (ci[0] > 1 or ci[1] < 1) else 0.5
    rel = 1.0 if ins.stage in STAGES else 0.5
    return 0.4 * EVIDENCE_WEIGHTS[ins.evidence_type] * sig + 0.3 * rel + 0.3 * effect_strength(ins)


def score_lexicographic(ins: Insight) -> float:
    """Option C: evidence type first, then CI significance, then n (encoded as one sortable number)."""
    ci = ins.effect.get("ci")
    sig = 1 if ci and (ci[0] > 1 or ci[1] < 1) else 0
    return EVIDENCE_WEIGHTS[ins.evidence_type] * 1e6 + sig * 1e4 + min(ins.n_tests, 9999)


RANKINGS = {
    "A_evidence_log_n": score_evidence_log_n,
    "B_multicriteria": score_multicriteria,
    "C_lexicographic": score_lexicographic,
}


def rank(insights: list[Insight], method: str = "A_evidence_log_n") -> list[Insight]:
    f = RANKINGS[method]
    for i in insights:
        i.score = round(f(i), 4)
    return sorted(insights, key=lambda i: i.score, reverse=True)
