"""Generates the fictional quarterly portfolio dataset.
A planted story: EMEA slipped openings (phasing), while NA ran hot on cost per store.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "portfolio_quarter.csv"

# region, plan_openings, actual_openings, plan_capex, actual_capex
ROWS = [
    ("UK & Ireland", 6, 5, 7800000, 6900000),
    ("Western Europe", 8, 6, 9600000, 7550000),
    ("Central Europe", 4, 4, 4200000, 4350000),
    ("North America", 5, 5, 6500000, 7450000),
    ("Asia Pacific", 3, 2, 4050000, 2800000),
]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region", "plan_openings", "actual_openings", "plan_capex", "actual_capex"])
        for r in ROWS:
            w.writerow(r)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
