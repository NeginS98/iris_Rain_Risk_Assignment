from __future__ import annotations
from .config import Thresholds

NO_DATA = "NO_DATA"
BELOW = "BELOW_THRESHOLD"
HEAVY = "HEAVY"
VERY_HEAVY = "VERY_HEAVY"
EXTREME = "EXTREME"


def classify(r1_mm: float | None, th: Thresholds) -> str:
    if r1_mm is None:
        return NO_DATA
    if r1_mm >= th.extreme:
        return EXTREME
    if r1_mm >= th.very_heavy:
        return VERY_HEAVY
    if r1_mm >= th.heavy: 
        return HEAVY
    return BELOW
