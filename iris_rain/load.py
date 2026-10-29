from __future__ import annotations
import csv
from pathlib import Path
from .classify import classify
from .config import Config

DDL = """
CREATE SCHEMA IF NOT EXISTS {schema};
CREATE TABLE IF NOT EXISTS {schema}.{table} (
    station_id        INTEGER      NOT NULL,
    observation_hour  TIMESTAMPTZ  NOT NULL,
    r1_mm             DOUBLE PRECISION,
    quality_level     SMALLINT,
    risk_class        TEXT         NOT NULL,
    source_file       TEXT         NOT NULL,
    loaded_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (station_id, observation_hour)
);
"""
UPSERT = """
INSERT INTO {schema}.{table}
    (station_id, observation_hour, r1_mm, quality_level, risk_class, source_file)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (station_id, observation_hour) DO UPDATE SET
    r1_mm = EXCLUDED.r1_mm, quality_level = EXCLUDED.quality_level,
    risk_class = EXCLUDED.risk_class, source_file = EXCLUDED.source_file,
    loaded_at = now();
"""


def to_rows(observations, cfg: Config):
    return [
        (o.station_id, o.observation_hour, o.r1_mm, o.quality_level,
         classify(o.r1_mm, cfg.thresholds), o.source_file)
        for o in observations
    ]


def load_postgres(observations, cfg: Config, dsn: str) -> int:
    import psycopg  # lazy import so tests/dry-run need no DB driver
    rows = to_rows(observations, cfg)
    fmt = {"schema": cfg.schema, "table": cfg.table}
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(DDL.format(**fmt))
        cur.executemany(UPSERT.format(**fmt), rows)
    return len(rows)


def write_csv(observations, cfg: Config, path: Path) -> int:
    rows = to_rows(observations, cfg)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["station_id", "observation_hour", "r1_mm", "quality_level", "risk_class", "source_file"])
        w.writerows([(a, b.isoformat(), c, d, e, f) for a, b, c, d, e, f in rows])
    return len(rows)
