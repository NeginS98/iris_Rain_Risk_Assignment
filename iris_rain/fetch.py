
from __future__ import annotations
import re
from pathlib import Path
import requests

DATA_ADD = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/precipitation/recent/"


def download_station(station_id: int, dest: Path, timeout: int = 60) -> Path:
    listing = requests.get(DATA_ADD, timeout=timeout)
    listing.raise_for_status()
    m = re.search(rf"stundenwerte_RR_{station_id:05d}_\d+_\d+_akt\.zip", listing.text)
    if not m:
        raise LookupError(f"no recent precipitation file for station {station_id}")
    out = dest / m.group(0)
    r = requests.get(DATA_ADD + m.group(0), timeout=timeout)
    r.raise_for_status()
    out.write_bytes(r.content)
    return out
