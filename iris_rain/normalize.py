from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Iterable

from .models import MISSING_VALUE, Observation, Reject

log = logging.getLogger(__name__)
REQUIRED = ("STATIONS_ID", "MESS_DATUM", "R1")


def _col_index(header_line: str) -> dict[str, int]:
    return {c.strip(): i for i, c in enumerate(header_line.split(";"))}


def normalize_lines(
    lines: Iterable[str], source_file: str, max_plausible_mm_h: float = 200.0
) -> tuple[list[Observation], list[Reject]]:
    obs: dict[tuple[int, datetime], Observation] = {}
    rejects: list[Reject] = []
    idx = {"STATIONS_ID": 0, "MESS_DATUM": 1, "QN_8": 2, "R1": 3}

    def reject(n: int, reason: str, raw: str):
        log.warning("%s:%d rejected (%s)", source_file, n, reason)
        rejects.append(Reject(source_file, n, reason, raw.rstrip("\n")))

    for n, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("STATIONS_ID"):
            idx = _col_index(line)
            if any(c not in idx for c in REQUIRED):
                raise ValueError(f"{source_file}: header lacks required columns {REQUIRED}")
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) <= max(idx[c] for c in REQUIRED):
            reject(n, "malformed_row", raw)
            continue
        try:
            station = int(parts[idx["STATIONS_ID"]])
        except ValueError:
            reject(n, "bad_station_id", raw)
            continue
        try:
            hour = datetime.strptime(parts[idx["MESS_DATUM"]], "%Y%m%d%H").replace(tzinfo=timezone.utc)
        except ValueError:
            reject(n, "bad_timestamp", raw)
            continue
        try:
            value = float(parts[idx["R1"]])
        except ValueError:
            reject(n, "bad_value", raw)
            continue
        if value == MISSING_VALUE:
            r1 = None
        elif value < 0 or value > max_plausible_mm_h:
            reject(n, "out_of_range", raw)
            continue
        else:
            r1 = value
        qn = None
        if "QN_8" in idx and idx["QN_8"] < len(parts):
            try:
                qn = int(parts[idx["QN_8"]])
            except ValueError:
                qn = None

        record = Observation(station, hour, r1, qn, source_file)
        key = (station, hour)
        if key in obs:
            kind = "duplicate" if obs[key].r1_mm == r1 else "duplicate_conflict"
            reject(n, kind, raw)  # first occurrence wins; conflicts are reported
            continue
        obs[key] = record
    return sorted(obs.values(), key=lambda o: (o.station_id, o.observation_hour)), rejects
