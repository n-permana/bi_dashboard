"""End-to-end ETL driver. Usage: python etl/run_etl.py"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# make sibling modules importable whether run as module or script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from extract import extract  # noqa: E402
from transform import build_dimensions_and_fact  # noqa: E402
from load import load  # noqa: E402


def main() -> None:
    t0 = time.time()
    print("=" * 60)
    print("Indonesia Tourism BI — ETL pipeline")
    print("=" * 60)

    raw = extract()
    tables = build_dimensions_and_fact(raw["arrivals"], raw["profile"])
    db_path = load(tables)

    print("-" * 60)
    print(f"Done in {time.time() - t0:.1f}s  ->  {db_path}")


if __name__ == "__main__":
    main()
