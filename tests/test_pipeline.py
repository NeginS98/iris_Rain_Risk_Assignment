from pathlib import Path
import pytest
from iris_rain.classify import BELOW, EXTREME, HEAVY, NO_DATA, VERY_HEAVY, classify
from iris_rain.config import Config, Thresholds
from iris_rain.load import to_rows
from iris_rain.normalize import normalize_lines
from iris_rain.report import build_report

FIXTURE = Path(__file__).parent / "fixtures" / "sample_rr.txt"
TH = Thresholds()


def run():
    return normalize_lines(FIXTURE.read_text().splitlines(), "sample_rr.txt")


def test_classification_boundaries():
    assert classify(None, TH) == NO_DATA          
    assert classify(0.0, TH) == BELOW
    assert classify(14.99, TH) == BELOW
    assert classify(15.0, TH) == HEAVY           
    assert classify(25.0, TH) == VERY_HEAVY
    assert classify(40.0, TH) == EXTREME


def test_accepted_records_and_missing_value():
    obs, _ = run()
    assert len(obs) == 6  # station 44: hours 12-16, station 71: hour 13
    missing = [o for o in obs if o.r1_mm is None]
    assert len(missing) == 1 and missing[0].observation_hour.hour == 16
    assert all(o.observation_hour.tzinfo is not None for o in obs)


def test_rejects_cover_all_bad_cases():
    _, rej = run()
    assert sorted(r.reason for r in rej) == sorted([
        "duplicate", "duplicate_conflict", "bad_value", "malformed_row",
        "bad_timestamp", "out_of_range",
    ])


def test_first_duplicate_wins():
    obs, _ = run()
    o = next(o for o in obs if o.station_id == 44 and o.observation_hour.hour == 13)
    assert o.r1_mm == 18.4


def test_rows_have_unique_keys():
    obs, _ = run()
    keys = [(r[0], r[1]) for r in to_rows(obs, Config())]
    assert len(keys) == len(set(keys))


def test_report_counts():
    obs, rej = run()
    rep = build_report(obs, rej, TH)
    assert rep["rows_no_data"] == 1 and rep["rows_rejected"] == 6
    assert rep["stations"][44]["peak_mm_h"] == 45.2


def test_refuses_non_staging_schema():
    with pytest.raises(ValueError):
        Config(schema="iris_core")


def test_bad_thresholds():
    with pytest.raises(ValueError):
        Thresholds(heavy=30, very_heavy=25, extreme=40)
