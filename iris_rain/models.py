from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

MISSING_VALUE = -999.0


@dataclass(frozen=True)
class Observation:
    station_id: int
    observation_hour: datetime  
    r1_mm: float | None        
    quality_level: int | None   
    source_file: str


@dataclass(frozen=True)
class Reject:
    source_file: str
    line_no: int
    reason: str
    raw: str
