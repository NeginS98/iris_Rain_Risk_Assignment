from __future__ import annotations
import argparse, json, logging, os, sys, zipfile
from pathlib import Path

from .config import load_config
from .load import load_postgres, write_csv
from .normalize import normalize_lines
from .report import build_report

log = logging.getLogger("iris_rain")


def _read_lines(path: Path):
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            name = next((n for n in zf.namelist() if n.startswith("produkt_rr_stunde")), None)
            if name is None:
                raise ValueError(f"{path}: no produkt_rr_stunde*.txt inside")
            return zf.read(name).decode("latin-1").splitlines()
    return path.read_text(encoding="latin-1").splitlines()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="iris_rain")
    p.add_argument("--input", nargs="+", required=True, type=Path, help="DWD .zip or product .txt files")
    p.add_argument("--config", default=None)
    p.add_argument("--out-dir", type=Path, default=Path("out"))
    p.add_argument("--dry-run", action="store_true", help="write CSV + report only, no database")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    cfg = load_config(args.config)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    observations, rejects = [], []
    for path in args.input:
        try:
            o, r = normalize_lines(_read_lines(path), path.name, cfg.max_plausible_mm_h)
        except Exception:
            log.exception("failed to process %s; continuing with remaining files", path)
            continue
        observations += o
        rejects += r
        log.info("%s: %d accepted, %d rejected", path.name, len(o), len(r))

    report = build_report(observations, rejects, cfg.thresholds)
    (args.out_dir / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (args.out_dir / "rejects.jsonl").write_text(
        "\n".join(json.dumps(r.__dict__) for r in rejects), encoding="utf-8")

    if args.dry_run:
        n = write_csv(observations, cfg, args.out_dir / "heavy_rainfall_risk.csv")
        log.info("dry-run: wrote %d rows to CSV", n)
        return 0
    dsn = os.environ.get("IRIS_STAGING_DSN")
    if not dsn:
        log.error("IRIS_STAGING_DSN is not set")
        return 2
    n = load_postgres(observations, cfg, dsn)
    log.info("upserted %d rows into %s.%s", n, cfg.schema, cfg.table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
