from __future__ import annotations
from dataclasses import dataclass, field
import re
import yaml


@dataclass(frozen=True)
class Thresholds:
    heavy: float = 15.0
    very_heavy: float = 25.0
    extreme: float = 40.0

    def __post_init__(self):
        if not (0 < self.heavy < self.very_heavy < self.extreme):
            raise ValueError("thresholds must satisfy 0 < heavy < very_heavy < extreme")


@dataclass(frozen=True)
class Config:
    thresholds: Thresholds = field(default_factory=Thresholds)
    max_plausible_mm_h: float = 200.0
    schema: str = "iris_staging"
    table: str = "heavy_rainfall_risk"

    def __post_init__(self):
        # Safety guard: only isolated staging schemas, valid SQL identifiers only.
        if not self.schema.startswith("iris_staging"):
            raise ValueError("refusing to write outside an iris_staging* schema")
        for name in (self.schema, self.table):
            if not re.fullmatch(r"[a-z_][a-z0-9_]*", name):
                raise ValueError(f"invalid SQL identifier: {name!r}")


def load_config(path: str | None = None) -> Config:
    if not path:
        return Config()
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    th = Thresholds(**raw.get("thresholds", {}))
    kwargs = {k: raw[k] for k in ("max_plausible_mm_h", "schema", "table") if k in raw}
    return Config(thresholds=th, **kwargs)
