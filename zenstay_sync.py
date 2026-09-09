#!/usr/bin/env python3
"""Casa Yano daily sync: install fresh ZenStay exports, rebuild, verify, ship.

The four ZenStay exports are plain authenticated GETs. A logged-in browser
session is required to fetch them (see DOWNLOAD_URLS below); this script picks
up whatever those downloads left in ~/Downloads and does everything after.

Run:  python3 zenstay_sync.py [--no-push] [--dry-run]

Exit codes: 0 ok, 1 precondition failed (nothing changed), 2 build failed.
"""
import argparse
import calendar
import json
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

SITE = Path(__file__).resolve().parent
DATA = SITE / "data"
DOWNLOADS = Path.home() / "Downloads"
ARCHIVE = DATA / "_superseded"

PROPERTY_ROUTE_ID = "44263"   # /auth/owner/... routes
PROPERTY_REPORT_ID = "44269"  # reports/detailed-expense ?property=

# Fetch these in a logged-in browser, then run this script.
def download_urls(today: date) -> dict:
    base = "https://app.zenstay.com/auth/owner"
    year_end = date(today.year, 12, 31)
    return {
        "current-bookings":  f"{base}/property/{PROPERTY_ROUTE_ID}/current-bookings/get/download/csv",
        "past-bookings":     f"{base}/property/{PROPERTY_ROUTE_ID}/past-bookings/get/download/csv",
        "upcoming-bookings": f"{base}/property/{PROPERTY_ROUTE_ID}/upcoming-bookings/get/download/csv",
        "detailed-expense": (
            f"{base}/reports/detailed-expense/download"
            f"?property={PROPERTY_REPORT_ID}&from=2025-12-01&to={year_end:%Y-%m-%d}"
            f"&format=csv&year={today.year}-01-01"
        ),
    }

# ZenStay download name -> canonical name in data/. Chrome appends " (N)" on
# repeat downloads, so match on prefix and take the newest.
BOOKING_FILES = {
    "current-bookings": "current-bookings.csv",
    "past-bookings": "past-bookings.csv",
    "upcoming-bookings": "upcoming-bookings.csv",
}
MIN_BYTES = {"current-bookings": 100, "past-bookings": 20_000, "upcoming-bookings": 2_000}


def newest(prefix: str, suffix: str = ".csv") -> Path | None:
    hits = [p for p in DOWNLOADS.glob(f"{prefix}*{suffix}") if p.is_file()]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def read_metrics() -> dict:
    js = (SITE / "public" / "data.js").read_text()
    blob = json.loads(js[js.find("{"): js.rfind("}") + 1])
    pf, sm = blob["proForma"], blob["summary"]
    return {
        "bookings": sm["totalBookings"], "gross": sm["totalGross"],
        "adr": sm["blendedAdr"], "occ": sm["totalOccupancy"],
        "pfGross": pf["gross"], "noiCash": pf["noiCash"],
        "noiNormalized": pf["noiNormalized"], "closedMonths": pf["closedMonths"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-age-hours", type=float, default=6.0,
                    help="reject downloads older than this")
    args = ap.parse_args()
    today = date.today()
    now = datetime.now().timestamp()

    print("Casa Yano sync", today)
    for name, url in download_urls(today).items():
        print(f"  {name}: {url}")

    # ---- locate and validate fresh downloads -------------------------------
    staged: list[tuple[Path, Path]] = []
    for prefix, canonical in BOOKING_FILES.items():
        src = newest(prefix)
        if src is None:
            print(f"MISSING: no {prefix}*.csv in ~/Downloads", file=sys.stderr)
            return 1
        age_h = (now - src.stat().st_mtime) / 3600
        if age_h > args.max_age_hours:
            print(f"STALE: {src.name} is {age_h:.1f}h old", file=sys.stderr)
            return 1
        if src.stat().st_size < MIN_BYTES[prefix]:
            print(f"TOO SMALL: {src.name} is {src.stat().st_size}b", file=sys.stderr)
            return 1
        staged.append((src, DATA / canonical))

    de_src = newest("DE-")
    if de_src is None:
        print("MISSING: no DE-*.csv in ~/Downloads", file=sys.stderr)
        return 1
    if (now - de_src.stat().st_mtime) / 3600 > args.max_age_hours:
        print(f"STALE: {de_src.name}", file=sys.stderr)
        return 1
    staged.append((de_src, DATA / de_src.name))

    before = read_metrics()

    if args.dry_run:
        for s, d in staged:
            print(f"  would install {s.name} -> {d.name}")
        return 0

    # ---- install ----------------------------------------------------------
    ARCHIVE.mkdir(exist_ok=True)
    for old in DATA.glob("DE-*.csv"):
        if old.name != de_src.name:
            shutil.move(str(old), ARCHIVE / old.name)
            print(f"  archived superseded {old.name}")
    # exactly one file per booking keyword or build.py's find_csv picks the wrong one
    for prefix in BOOKING_FILES:
        for old in DATA.glob(f"{prefix}*.csv"):
            old.unlink()
    for src, dst in staged:
        shutil.copy2(src, dst)
        print(f"  installed {dst.name}")

    # ---- build ------------------------------------------------------------
    r = subprocess.run([sys.executable, "build.py"], cwd=SITE,
                       capture_output=True, text=True)
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
        return 2

    after = read_metrics()
    print("\n           metric        before          after")
    for k in ("bookings", "gross", "adr", "pfGross", "noiCash", "noiNormalized"):
        print(f"  {k:>16} {before[k]:>13,} {after[k]:>14,}")

    # ---- sanity gates -----------------------------------------------------
    if after["bookings"] < before["bookings"] - 5:
        print("ABORT: booking count dropped by more than 5; not shipping.", file=sys.stderr)
        return 1
    if after["noiCash"] <= 0:
        print("ABORT: non-positive NOI.", file=sys.stderr)
        return 1
    if after == before:
        print("No change in metrics; nothing to commit.")
        return 0

    # ---- ship -------------------------------------------------------------
    subprocess.run(["git", "add", "public/data.js"], cwd=SITE, check=True)
    if not subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=SITE).returncode:
        print("data.js unchanged; nothing to commit.")
        return 0
    msg = (f"Update dashboard {today:%-m/%-d}: {after['bookings']} bookings, "
           f"${after['gross']:,.0f} gross, ${after['adr']:,.0f} ADR\n\n"
           f"FY2026 pro forma gross ${after['pfGross']:,.0f}, "
           f"NOI cash ${after['noiCash']:,.0f}, normalized ${after['noiNormalized']:,.0f}.\n"
           f"QBO closed months: {after['closedMonths']}.\n\n"
           "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    subprocess.run(["git", "commit", "-m", msg], cwd=SITE, check=True)
    if args.no_push:
        print("Committed. --no-push set, not pushing.")
        return 0
    subprocess.run(["git", "push", "origin", "main"], cwd=SITE, check=True)
    print("Pushed. Vercel will deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
