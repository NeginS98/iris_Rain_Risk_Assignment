from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import asdict
from .classify import NO_DATA, classify
from .config import Thresholds


def build_report(observations, rejects, th: Thresholds) -> dict:
    per_station: dict[int, dict] = defaultdict(
        lambda: {"hours": 0, "missing": 0, "peak_mm_h": None, "classes": Counter()})
    for o in observations:
        s = per_station[o.station_id]
        s["hours"] += 1
        s["classes"][classify(o.r1_mm, th)] += 1
        if o.r1_mm is None:
            s["missing"] += 1
        elif s["peak_mm_h"] is None or o.r1_mm > s["peak_mm_h"]:
            s["peak_mm_h"] = o.r1_mm
    stations = {
        sid: {
            "hours": s["hours"], "missing": s["missing"], "peak_mm_h": s["peak_mm_h"],
            "coverage_pct": round(100 * (s["hours"] - s["missing"]) / s["hours"], 1),
            "classes": dict(s["classes"]),
        }
        for sid, s in sorted(per_station.items())
    }
    return {
        "rows_accepted": len(observations),
        "rows_no_data": sum(1 for o in observations if classify(o.r1_mm, th) == NO_DATA),
        "rows_rejected": len(rejects),
        "rejects_by_reason": dict(Counter(r.reason for r in rejects)),
        "thresholds_mm_h": asdict(th),
        "stations": stations,
        "assumptions": [
            "R1 is hourly precipitation height in mm (DWD); timestamps are UTC.",
            "Missing (-999) is never classified; it is stored as NO_DATA.",
            "On duplicate station+hour the first record wins; conflicts are reported.",
            "Preliminary engineering screening, not certified design.",
        ],
    }
