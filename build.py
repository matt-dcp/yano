#!/usr/bin/env python3
"""
Casa Yano Dashboard Builder
============================
Reads booking + expense CSVs, computes all metrics, writes public/data.js.

Usage:
  1. Drop CSV exports into the data/ folder:
     - bookings-current.csv  (or any file containing "current" in the name)
     - bookings-past.csv     (or any file containing "past")
     - bookings-upcoming.csv (or any file containing "upcoming")
     - expenses.csv          (or any file containing "expense" or "paid reimbursed")
  2. Run: python build.py
  3. Deploy: vercel --prod
"""

import csv
import json
import os
import re
import calendar
from datetime import datetime, date
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
OUTPUT = Path(__file__).parent / "public" / "data.js"
FORECAST_HISTORY = DATA_DIR / "forecast_history.json"

# ════════════════════════════════════════════════════════════════
# CONFIG — Edit these when assumptions change
# ════════════════════════════════════════════════════════════════
OPENING_DATE = date(2025, 12, 18)
NUM_UNITS = 6
MGMT_FEE_PCT = 0.10          # 10% of gross
PROPERTY_TAX_ANNUAL = 26679   # SB County 2025-26
INSURANCE_ANNUAL = 13500      # STR commercial policy
INTERNET_ANNUAL = 3000        # $250/mo
BOOKKEEPING_ANNUAL = 4200     # $350/mo
LANDSCAPE_ANNUAL = 6000       # $500/mo
LINEN_FFE_ANNUAL = 4800       # $400/mo
LICENSE_ANNUAL = 1200          # $100/mo
CONSUMABLES_ANNUAL = 4800     # $400/mo
OTHER_FIXED_ANNUAL = INTERNET_ANNUAL + BOOKKEEPING_ANNUAL + LANDSCAPE_ANNUAL + LINEN_FFE_ANNUAL + LICENSE_ANNUAL + CONSUMABLES_ANNUAL  # $24,000
SB_MEDIAN_ADR = 321
SB_TOP25_ADR = 521
SB_TYPICAL_MARGIN = 75
SB_TOP25_MARGIN = 85
SB_AVG_OTA_COMMISSION = 15

# Seasonal indices for Santa Barbara STR market
# These define the SHAPE of ADR and occupancy across the year, relative to
# the annual average (1.0). The actual LEVEL is auto-calibrated from closed-month
# actuals each time build.py runs — these just control the seasonal curve.
SB_ADR_SEASONAL = {
    1: 0.75, 2: 0.95, 3: 1.00, 4: 1.05, 5: 1.10, 6: 1.20,
    7: 1.25, 8: 1.20, 9: 0.95, 10: 0.90, 11: 0.90, 12: 0.95,
}
SB_OCC_SEASONAL = {
    1: 0.90, 2: 0.97, 3: 1.00, 4: 0.97, 5: 1.00, 6: 1.07,
    7: 1.10, 8: 1.07, 9: 0.90, 10: 0.85, 11: 0.88, 12: 0.93,
}
MAX_OCCUPANCY_PCT = 92  # cap for projected occupancy

# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════
def parse_dollar(s):
    """Parse '$1,234.56' or '$1,234.56 ($617.28)' → float. Returns first number."""
    if not s or s.strip() in ("", "-"):
        return 0.0
    m = re.search(r'[\$]?([\d,]+\.?\d*)', str(s).replace("−", "-"))
    if m:
        return float(m.group(1).replace(",", ""))
    return 0.0

def parse_adr_field(s):
    """Parse 'Gross (ADR)' field like '$553.81 ($553.81)' → (gross, adr_per_night)."""
    nums = re.findall(r'[\$]?([\d,]+\.?\d*)', str(s))
    if len(nums) >= 2:
        return float(nums[0].replace(",", "")), float(nums[1].replace(",", ""))
    elif len(nums) == 1:
        return float(nums[0].replace(",", "")), float(nums[0].replace(",", ""))
    return 0.0, 0.0

def parse_booking_date(s):
    """Parse '02/05/26 at 3:00 PM' → date object."""
    if not s or not s.strip():
        return None
    s = s.strip()
    for fmt in ("%m/%d/%y at %I:%M %p", "%m/%d/%y at %I:%M%p", "%m/%d/%Y at %I:%M %p",
                "%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def parse_expense_date(s):
    """Parse expense date in various formats."""
    if not s or not s.strip():
        return None
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def month_key(d):
    """date → 'Jan '26' style key."""
    if not d:
        return None
    return d.strftime("%b '%y")

def month_sort_key(mk):
    """Sort month keys chronologically."""
    try:
        return datetime.strptime(mk, "%b '%y")
    except:
        return datetime.min

def find_csv(keyword):
    """Find a CSV in data/ folder matching a keyword."""
    for f in DATA_DIR.iterdir():
        if f.suffix.lower() == ".csv" and keyword.lower() in f.name.lower():
            return f
    return None

# ════════════════════════════════════════════════════════════════
# PARSE BOOKINGS
# ════════════════════════════════════════════════════════════════
def load_bookings():
    bookings = []
    for keyword in ["current", "past", "upcoming"]:
        csv_path = find_csv(keyword)
        if not csv_path:
            print(f"  Warning: No CSV found for '{keyword}' bookings")
            continue
        print(f"  Loading {csv_path.name}...")
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                gross_raw, adr_per_night = parse_adr_field(row.get("Gross (ADR)", ""))
                start = parse_booking_date(row.get("Start Date", ""))
                end = parse_booking_date(row.get("End Date", ""))
                nights = (end - start).days if start and end else 1
                if nights < 1:
                    nights = 1
                bookings.append({
                    "gross": gross_raw,
                    "adr": adr_per_night,
                    "paid": parse_dollar(row.get("Paid", "")),
                    "ota_commission": parse_dollar(row.get("OTA Commission", "")),
                    "fees": parse_dollar(row.get("Fees", "")),
                    "taxes": parse_dollar(row.get("Taxes", "")),
                    "processing": parse_dollar(row.get("Processing", "")),
                    "to_owner": parse_dollar(row.get("To Owner", "")),
                    "start": start,
                    "end": end,
                    "nights": nights,
                    "booked_at": parse_booking_date(row.get("Booked At", "")),
                    "source": (row.get("Source", "") or "").strip(),
                    "unit": (row.get("Unit", "") or "").strip(),
                    "type": keyword,
                })
    print(f"  Total bookings loaded: {len(bookings)}")
    return bookings

# ════════════════════════════════════════════════════════════════
# PARSE EXPENSES
# ════════════════════════════════════════════════════════════════
def load_expenses():
    csv_path = find_csv("expense") or find_csv("paid") or find_csv("reimburs") or find_csv("DE-")
    if not csv_path:
        print("  Warning: No expense CSV found")
        return []
    print(f"  Loading {csv_path.name}...")
    expenses = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Support both "Amount" (old format) and "Expense" (new DE- format) columns
            amount_raw = row.get("Amount", "") or row.get("Expense", "") or ""
            amount_str = str(amount_raw).strip()
            # Skip rows with no amount, summary/total rows, or unit section headers
            if not amount_str or amount_str == "":
                continue
            cat_raw = (row.get("Category", "") or "").strip()
            date_raw = (row.get("Date", "") or "").strip()
            # Skip rows that are just totals (no date, no category)
            if not date_raw and not cat_raw:
                continue
            amount = parse_dollar(amount_raw)
            # Check for negative (refund) — handles both ($81.90) and -81.9 formats
            if "(" in amount_str or (amount_str.startswith("-") and amount > 0):
                amount = -abs(amount)
            expenses.append({
                "date": parse_expense_date(date_raw),
                "category": cat_raw,
                "vendor": (row.get("Vendor", "") or "").strip(),
                "amount": amount,
            })
    print(f"  Total expenses loaded: {len(expenses)}")
    return expenses

# ════════════════════════════════════════════════════════════════
# COMPUTE METRICS
# ════════════════════════════════════════════════════════════════
def classify_expense(cat):
    """Map raw expense category to our buckets."""
    cat_lower = cat.lower()
    # "Maintenance / Cleaning" → Cleaning (check specific subcategory after slash)
    if "/" in cat_lower:
        sub = cat_lower.split("/")[-1].strip()
        if "clean" in sub:
            return "Cleaning"
        elif "supply" in sub or "supplies" in sub or "linen" in sub or "amenities" in sub:
            return "Supplies"
        elif "appliance" in sub:
            return "CapEx"
    if "clean" in cat_lower:
        return "Cleaning"
    elif "supply" in cat_lower or "supplies" in cat_lower or "linen" in cat_lower or "amenities" in cat_lower:
        return "Supplies"
    elif "capital" in cat_lower or "appliance" in cat_lower:
        return "CapEx"
    elif "market" in cat_lower or "advertis" in cat_lower:
        return "Marketing"
    elif "tax" in cat_lower or "license" in cat_lower or "permit" in cat_lower:
        return "Taxes & Licenses"
    elif "maint" in cat_lower or "repair" in cat_lower:
        return "Maintenance"
    elif "management" in cat_lower or "hospitality" in cat_lower:
        return "Management"
    elif "reconciliation" in cat_lower:
        return "OTA Reconciliation"
    elif "guest relation" in cat_lower or "guest credit" in cat_lower:
        return "Guest Credits"
    else:
        return "Other"

def normalize_source(src):
    """Normalize booking source names."""
    src_lower = src.lower()
    if "airbnb" in src_lower:
        return "Airbnb"
    elif "expedia" in src_lower:
        return "Expedia"
    elif "booking" in src_lower:
        return "Booking.com"
    elif "zenstay" in src_lower or "zen stay" in src_lower:
        return "ZenStay"
    elif "casayano" in src_lower or "direct" in src_lower or "www." in src_lower:
        return "Direct"
    elif "vhr" in src_lower:
        return "VHR"
    else:
        return src or "Other"

def compute(bookings, expenses):
    today = date.today()
    days_since_launch = (today - OPENING_DATE).days

    # ── Totals ──
    total_gross = sum(b["gross"] for b in bookings)
    total_to_owner = sum(b["to_owner"] for b in bookings)
    total_ota = sum(b["ota_commission"] for b in bookings)
    total_taxes = sum(b["taxes"] for b in bookings)
    total_processing = sum(b["processing"] for b in bookings)
    total_nights = sum(b["nights"] for b in bookings)
    total_bookings = len(bookings)
    blended_adr = total_gross / total_nights if total_nights else 0
    owner_margin = (total_to_owner / total_gross * 100) if total_gross else 0
    ota_pct = (total_ota / total_gross * 100) if total_gross else 0
    avg_stay = total_nights / total_bookings if total_bookings else 0

    # Lead time
    lead_times = []
    for b in bookings:
        if b["booked_at"] and b["start"]:
            lt = (b["start"] - b["booked_at"]).days
            if lt >= 0:
                lead_times.append(lt)
    avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0

    # ── Monthly data ──
    monthly = defaultdict(lambda: {"gross": 0, "toOwner": 0, "bookings": 0, "nights": 0})
    for b in bookings:
        mk = month_key(b["start"])
        if mk:
            monthly[mk]["gross"] += b["gross"]
            monthly[mk]["toOwner"] += b["to_owner"]
            monthly[mk]["bookings"] += 1
            monthly[mk]["nights"] += b["nights"]

    sorted_months = sorted(monthly.keys(), key=month_sort_key)
    monthly_data = []
    for mk in sorted_months:
        m = monthly[mk]
        adr = m["gross"] / m["nights"] if m["nights"] else 0
        # Calculate available nights for occupancy & RevPAR
        try:
            mk_date = datetime.strptime(mk, "%b '%y")
            mk_year, mk_month = mk_date.year, mk_date.month
            if mk_year < 100:
                mk_year += 2000
            total_days = calendar.monthrange(mk_year, mk_month)[1]
        except:
            total_days = 30
        # Handle partial opening month (Dec '25 — opened Dec 18)
        if mk_year == OPENING_DATE.year and mk_month == OPENING_DATE.month:
            total_days = total_days - OPENING_DATE.day + 1  # 14 days for Dec 18-31
        avail_nights = NUM_UNITS * total_days
        occupancy = round(m["nights"] / avail_nights * 100, 1) if avail_nights else 0
        revpar = round(m["gross"] / avail_nights) if avail_nights else 0
        monthly_data.append({
            "month": mk,
            "gross": round(m["gross"]),
            "toOwner": round(m["toOwner"]),
            "bookings": m["bookings"],
            "adr": round(adr),
            "nights": m["nights"],
            "occupancy": occupancy,
            "revpar": revpar,
        })

    # ── Source data ──
    by_source = defaultdict(lambda: {"bookings": 0, "revenue": 0})
    for b in bookings:
        src = normalize_source(b["source"])
        by_source[src]["bookings"] += 1
        by_source[src]["revenue"] += b["gross"]

    source_data = []
    for src, d in sorted(by_source.items(), key=lambda x: -x[1]["bookings"]):
        source_data.append({
            "name": src,
            "bookings": d["bookings"],
            "pct": round(d["bookings"] / total_bookings * 100, 1) if total_bookings else 0,
            "revenue": round(d["revenue"]),
        })

    # OTA vs Direct
    ota_bookings = sum(1 for b in bookings if normalize_source(b["source"]) not in ("Direct",))
    direct_bookings = total_bookings - ota_bookings
    ota_booking_pct = round(ota_bookings / total_bookings * 100, 1) if total_bookings else 0

    # ── Unit data ──
    by_unit = defaultdict(lambda: {"bookings": 0, "toOwner": 0, "gross": 0, "nights": 0})
    for b in bookings:
        u = b["unit"] or "Unknown"
        by_unit[u]["bookings"] += 1
        by_unit[u]["toOwner"] += b["to_owner"]
        by_unit[u]["gross"] += b["gross"]
        by_unit[u]["nights"] += b["nights"]

    unit_data = []
    for u in sorted(by_unit.keys()):
        d = by_unit[u]
        adr = d["gross"] / d["nights"] if d["nights"] else 0
        avg_rev = d["toOwner"] / d["bookings"] if d["bookings"] else 0
        avg_s = d["nights"] / d["bookings"] if d["bookings"] else 0
        unit_data.append({
            "unit": u,
            "bookings": d["bookings"],
            "toOwner": round(d["toOwner"]),
            "avgRev": round(avg_rev),
            "adr": round(adr),
            "nights": d["nights"],
            "avgStay": round(avg_s, 1),
        })

    # ── Expense data ──
    total_expense = sum(e["amount"] for e in expenses)

    by_cat = defaultdict(float)
    for e in expenses:
        by_cat[classify_expense(e["category"])] += e["amount"]

    expense_categories = []
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        expense_categories.append({
            "category": cat,
            "amount": round(amt),
            "pct": round(amt / total_expense * 100, 1) if total_expense else 0,
        })

    # Monthly expenses
    exp_monthly = defaultdict(lambda: {"total": 0, "cleaning": 0, "supplies": 0,
                                        "capex": 0, "maint": 0, "marketing": 0,
                                        "mgmt": 0, "taxes": 0, "other": 0})
    cat_map = {"Cleaning": "cleaning", "Supplies": "supplies", "CapEx": "capex",
               "Maintenance": "maint", "Marketing": "marketing",
               "Management": "mgmt", "Taxes & Licenses": "taxes"}
    for e in expenses:
        mk = month_key(e["date"])
        if mk:
            bucket = cat_map.get(classify_expense(e["category"]), "other")
            exp_monthly[mk]["total"] += e["amount"]
            exp_monthly[mk][bucket] += e["amount"]

    sorted_exp_months = sorted(exp_monthly.keys(), key=month_sort_key)
    expense_monthly = []
    for mk in sorted_exp_months:
        d = exp_monthly[mk]
        expense_monthly.append({
            "month": mk,
            **{k: round(v) for k, v in d.items()},
        })

    # Top vendors
    by_vendor = defaultdict(lambda: {"amount": 0, "category": ""})
    for e in expenses:
        v = e["vendor"] or "Unknown"
        by_vendor[v]["amount"] += e["amount"]
        by_vendor[v]["category"] = classify_expense(e["category"])

    top_vendors = []
    for v, d in sorted(by_vendor.items(), key=lambda x: -x[1]["amount"])[:10]:
        top_vendors.append({
            "vendor": v,
            "amount": round(d["amount"]),
            "category": d["category"],
        })

    # ── One-time vs recurring ──
    cleaning_total = by_cat.get("Cleaning", 0)
    # Cost per turn = cleaning spend / realized bookings (past + current, not upcoming)
    realized_bookings = sum(1 for b in bookings if b["type"] in ("past", "current"))
    cost_per_turn = round(cleaning_total / realized_bookings) if realized_bookings and cleaning_total > 0 else 111

    # ── Dynamic Pro Forma ──
    # Auto-calibrates with each data upload: closed months use actual income + expenses,
    # future months project from de-seasonalized baselines × seasonal shape.
    # The more months that close, the more accurate forward projections become.
    MONTH_NAMES_PF = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    # Build actual revenue lookup keyed by month abbreviation (2026 only)
    actual_rev = {}
    for md in monthly_data:
        parts = md["month"].split(" '")
        if len(parts) == 2 and int(parts[1]) + 2000 == 2026:
            actual_rev[parts[0]] = md

    # Build actual expense lookup
    actual_exp_lookup = {}
    for ed in expense_monthly:
        parts = ed["month"].split(" '")
        if len(parts) == 2 and int(parts[1]) + 2000 == 2026:
            actual_exp_lookup[parts[0]] = ed

    # Classify months as closed / current / future
    # A month is "closed" once we reach its last day (operating activity is locked).
    month_status = {}
    for i, name in enumerate(MONTH_NAMES_PF):
        mn = i + 1
        m_end = date(2026, mn, calendar.monthrange(2026, mn)[1])
        m_start = date(2026, mn, 1)
        if m_end <= today:
            month_status[name] = "closed"
        elif m_start <= today < m_end:
            month_status[name] = "current"
        else:
            month_status[name] = "future"

    # Collect closed-month metrics for baseline calibration
    closed_metrics = []
    for name in MONTH_NAMES_PF:
        if month_status[name] == "closed" and name in actual_rev:
            mn = MONTH_NAMES_PF.index(name) + 1
            closed_metrics.append({
                "num": mn, "adr": actual_rev[name]["adr"],
                "occ": actual_rev[name]["occupancy"],
            })

    # De-seasonalize closed months to find baseline ADR and occupancy.
    # Dividing each month's actual by its seasonal index strips out seasonality,
    # revealing the underlying performance level. Averaging these gives a stable
    # baseline that improves as more months close.
    if closed_metrics:
        ds_adrs = [cm["adr"] / SB_ADR_SEASONAL[cm["num"]] for cm in closed_metrics]
        ds_occs = [cm["occ"] / SB_OCC_SEASONAL[cm["num"]] for cm in closed_metrics]
        baseline_adr = sum(ds_adrs) / len(ds_adrs)
        baseline_occ = sum(ds_occs) / len(ds_occs)
    else:
        baseline_adr = float(SB_MEDIAN_ADR)
        baseline_occ = 75.0

    # Owner margin from actual booking data
    actual_margin = total_to_owner / total_gross if total_gross else 0.89

    # Expense baselines from closed months
    # Management is deducted separately as 10% of gross — excluded from OpEx here
    closed_opex_non_clean = []
    clean_per_turn_monthly = []
    for name in MONTH_NAMES_PF:
        if month_status[name] == "closed" and name in actual_exp_lookup and name in actual_rev:
            exp = actual_exp_lookup[name]
            non_clean = exp["total"] - exp["cleaning"] - exp.get("mgmt", 0)
            closed_opex_non_clean.append(non_clean)
            if actual_rev[name]["bookings"] > 0 and exp["cleaning"] > 0:
                clean_per_turn_monthly.append(exp["cleaning"] / actual_rev[name]["bookings"])

    # Non-cleaning OpEx: trailing average, dropping first month if it's a startup outlier
    if len(closed_opex_non_clean) >= 2:
        first = closed_opex_non_clean[0]
        rest_avg = sum(closed_opex_non_clean[1:]) / len(closed_opex_non_clean[1:])
        trailing_non_clean = rest_avg if first > rest_avg * 1.4 else (
            sum(closed_opex_non_clean) / len(closed_opex_non_clean))
    elif closed_opex_non_clean:
        trailing_non_clean = closed_opex_non_clean[0]
    else:
        trailing_non_clean = 5000

    # Cleaning cost per turn: drop first month if it's a startup outlier
    if len(clean_per_turn_monthly) >= 2:
        first = clean_per_turn_monthly[0]
        rest_avg = sum(clean_per_turn_monthly[1:]) / len(clean_per_turn_monthly[1:])
        clean_cost = rest_avg if first > rest_avg * 1.3 else (
            sum(clean_per_turn_monthly) / len(clean_per_turn_monthly))
    elif clean_per_turn_monthly:
        clean_cost = clean_per_turn_monthly[0]
    else:
        clean_cost = cost_per_turn

    # ── Build pro forma monthly entries ──
    pf_monthly = []
    pf_total_cleaning = 0
    pf_total_other_opex = 0

    for i, name in enumerate(MONTH_NAMES_PF):
        mn = i + 1
        status = month_status[name]
        avail_days = calendar.monthrange(2026, mn)[1]
        avail_nights = NUM_UNITS * avail_days

        if status in ("closed", "current") and name in actual_rev:
            # Use actual income + actual expenses from the uploaded data
            rev = actual_rev[name]
            exp = actual_exp_lookup.get(name)
            if exp:
                month_opex = exp["total"] - exp.get("mgmt", 0)
                month_clean = exp["cleaning"]
            else:
                month_opex = 0
                month_clean = 0
            pf_total_cleaning += month_clean
            pf_total_other_opex += month_opex - month_clean
            pf_monthly.append({
                "month": name, "adr": rev["adr"], "occ": rev["occupancy"],
                "gross": rev["gross"], "netOwner": rev["toOwner"],
                "opex": round(month_opex), "noi": round(rev["toOwner"] - month_opex),
                "bookings": rev["bookings"],
                "source": "actual" if status == "closed" else "booked",
            })
        else:
            # Project from de-seasonalized baseline × seasonal index
            proj_adr = round(baseline_adr * SB_ADR_SEASONAL[mn])
            proj_occ = min(round(baseline_occ * SB_OCC_SEASONAL[mn], 1), MAX_OCCUPANCY_PCT)
            proj_nights = round(avail_nights * proj_occ / 100)
            proj_gross = round(proj_adr * proj_nights)
            proj_net = round(proj_gross * actual_margin)
            proj_bookings = max(1, round(proj_nights / avg_stay)) if avg_stay else round(proj_nights / 2.7)
            proj_cleaning = round(clean_cost * proj_bookings)
            proj_opex = proj_cleaning + round(trailing_non_clean)
            pf_total_cleaning += proj_cleaning
            pf_total_other_opex += round(trailing_non_clean)
            pf_monthly.append({
                "month": name, "adr": proj_adr, "occ": proj_occ,
                "gross": proj_gross, "netOwner": proj_net,
                "opex": proj_opex, "noi": proj_net - proj_opex,
                "bookings": proj_bookings, "source": "projected",
            })

    # ── Pro forma totals ──
    pf_gross = sum(m["gross"] for m in pf_monthly)
    pf_net_owner = sum(m["netOwner"] for m in pf_monthly)
    pf_opex = sum(m["opex"] for m in pf_monthly)
    pf_noi_before_fixed = pf_net_owner - pf_opex
    mgmt_fee = round(pf_gross * MGMT_FEE_PCT)
    pf_noi_after_known = pf_noi_before_fixed - mgmt_fee - PROPERTY_TAX_ANNUAL - INSURANCE_ANNUAL - OTHER_FIXED_ANNUAL
    pf_avg_occ = sum(m["occ"] for m in pf_monthly) / 12
    pf_avg_adr = round(sum(m["adr"] for m in pf_monthly) / 12)

    # ── Forecast Accuracy Feedback Loop ──
    # Each build saves a snapshot of projected months. When those months later close,
    # we compare the prior projection against actuals to measure forecast accuracy.
    # This scorecard helps calibrate confidence and reveals systematic bias.
    forecast_history = {}
    if FORECAST_HISTORY.exists():
        try:
            with open(FORECAST_HISTORY, "r") as fh:
                forecast_history = json.loads(fh.read())
        except (json.JSONDecodeError, IOError):
            forecast_history = {}

    # Score prior forecasts against newly-closed actuals
    forecast_scorecard = []
    for entry in pf_monthly:
        name = entry["month"]
        if entry["source"] != "actual":
            continue
        # Check if we had a prior projection for this now-actual month
        prior = forecast_history.get(name)
        if not prior:
            continue
        actual_gross = entry["gross"]
        actual_adr = entry["adr"]
        actual_occ = entry["occ"]
        actual_opex = entry["opex"]
        forecast_scorecard.append({
            "month": name,
            "forecastDate": prior.get("forecastDate", "unknown"),
            "projGross": prior["gross"], "actGross": actual_gross,
            "grossErr": round((prior["gross"] - actual_gross) / actual_gross * 100, 1) if actual_gross else 0,
            "projAdr": prior["adr"], "actAdr": actual_adr,
            "adrErr": round((prior["adr"] - actual_adr) / actual_adr * 100, 1) if actual_adr else 0,
            "projOcc": prior["occ"], "actOcc": actual_occ,
            "occErr": round((prior["occ"] - actual_occ) / actual_occ * 100, 1) if actual_occ else 0,
            "projOpex": prior["opex"], "actOpex": actual_opex,
            "opexErr": round((prior["opex"] - actual_opex) / actual_opex * 100, 1) if actual_opex else 0,
            "type": "snapshot",
        })

    # Back-test: also score the model's current seasonal projection against closed actuals.
    # This shows how well the seasonal model fits even without prior snapshots.
    backtest_scorecard = []
    for entry in pf_monthly:
        name = entry["month"]
        if entry["source"] != "actual":
            continue
        mn = MONTH_NAMES_PF.index(name) + 1
        avail_nights = NUM_UNITS * calendar.monthrange(2026, mn)[1]
        model_adr = round(baseline_adr * SB_ADR_SEASONAL[mn])
        model_occ = min(round(baseline_occ * SB_OCC_SEASONAL[mn], 1), MAX_OCCUPANCY_PCT)
        model_nights = round(avail_nights * model_occ / 100)
        model_gross = round(model_adr * model_nights)
        actual_gross = entry["gross"]
        actual_adr = entry["adr"]
        actual_occ = entry["occ"]
        backtest_scorecard.append({
            "month": name,
            "forecastDate": "model",
            "projGross": model_gross, "actGross": actual_gross,
            "grossErr": round((model_gross - actual_gross) / actual_gross * 100, 1) if actual_gross else 0,
            "projAdr": model_adr, "actAdr": actual_adr,
            "adrErr": round((model_adr - actual_adr) / actual_adr * 100, 1) if actual_adr else 0,
            "projOcc": model_occ, "actOcc": actual_occ,
            "occErr": round((model_occ - actual_occ) / actual_occ * 100, 1) if actual_occ else 0,
            "type": "backtest",
        })

    # Compute aggregate accuracy metrics — use snapshots if available, fall back to backtest
    scored = forecast_scorecard if forecast_scorecard else backtest_scorecard
    if scored:
        avg_gross_err = sum(abs(s["grossErr"]) for s in scored) / len(scored)
        avg_adr_err = sum(abs(s["adrErr"]) for s in scored) / len(scored)
        avg_occ_err = sum(abs(s["occErr"]) for s in scored) / len(scored)
        gross_bias = sum(s["grossErr"] for s in scored) / len(scored)
        forecast_accuracy = {
            "scoredMonths": len(scored),
            "mapeGross": round(avg_gross_err, 1),
            "mapeAdr": round(avg_adr_err, 1),
            "mapeOcc": round(avg_occ_err, 1),
            "biasGross": round(gross_bias, 1),  # positive = over-projecting
            "details": scored,
            "backtestDetails": backtest_scorecard,  # always include backtest
            "snapshotDetails": forecast_scorecard,  # empty until snapshots score
            "source": "snapshot" if forecast_scorecard else "backtest",
        }
    else:
        forecast_accuracy = {
            "scoredMonths": 0,
            "mapeGross": None, "mapeAdr": None, "mapeOcc": None,
            "biasGross": None, "details": [], "backtestDetails": [],
            "snapshotDetails": [], "source": None,
        }

    # Save current projections as the new snapshot for future scoring.
    # IMPORTANT: Only save the FIRST projection for each month — never overwrite.
    # This ensures we score the model's original call, not a revised one that had
    # the benefit of more data. This is what makes the feedback loop honest.
    build_date = today.isoformat()
    for entry in pf_monthly:
        name = entry["month"]
        if entry["source"] == "projected" and name not in forecast_history:
            forecast_history[name] = {
                "gross": entry["gross"], "adr": entry["adr"],
                "occ": entry["occ"], "opex": entry["opex"],
                "netOwner": entry["netOwner"], "noi": entry["noi"],
                "bookings": entry["bookings"],
                "forecastDate": build_date,
            }
    # Also track the latest projection separately so dashboard can show drift
    latest_projections = {}
    for entry in pf_monthly:
        name = entry["month"]
        if entry["source"] == "projected":
            latest_projections[name] = {
                "gross": entry["gross"], "adr": entry["adr"],
                "occ": entry["occ"], "forecastDate": build_date,
            }
    forecast_history["_latest"] = latest_projections

    # Persist the forecast history
    with open(FORECAST_HISTORY, "w") as fh:
        fh.write(json.dumps(forecast_history, indent=2))

    # Waterfall using actual deduction ratios from booking data
    tax_rate = (total_taxes / total_gross) if total_gross else 0.12
    proc_rate = (total_processing / total_gross) if total_gross else 0.025
    pf_total_ota = round(pf_gross * (ota_pct / 100))
    pf_total_tax = round(pf_gross * tax_rate)
    pf_total_proc = round(pf_gross * proc_rate)
    pf_waterfall = [
        {"name": "Gross Revenue", "value": pf_gross, "type": "positive"},
        {"name": "OTA Commissions", "value": -pf_total_ota, "type": "negative"},
        {"name": "Taxes (TOT)", "value": -pf_total_tax, "type": "negative"},
        {"name": "Processing", "value": -pf_total_proc, "type": "negative"},
        {"name": "Net to Owner", "value": pf_net_owner, "type": "subtotal"},
        {"name": "Cleaning", "value": -round(pf_total_cleaning), "type": "opex"},
        {"name": "Supplies/Maint/Other", "value": -round(pf_total_other_opex), "type": "opex"},
        {"name": "Mgmt Fee (10%)", "value": -mgmt_fee, "type": "mgmt"},
        {"name": "Property Tax", "value": -PROPERTY_TAX_ANNUAL, "type": "opex"},
        {"name": "Insurance", "value": -INSURANCE_ANNUAL, "type": "opex"},
        {"name": "Other Fixed (6 items)", "value": -OTHER_FIXED_ANNUAL, "type": "opex"},
        {"name": "NOI", "value": pf_noi_after_known, "type": "total"},
    ]

    # ── Benchmark data ──
    sb_comp = [
        {"metric": "ADR", "casaYano": round(blended_adr), "sbMedian": SB_MEDIAN_ADR, "sbTop25": SB_TOP25_ADR},
        {"metric": "Owner Margin", "casaYano": round(owner_margin, 1), "sbMedian": SB_TYPICAL_MARGIN, "sbTop25": SB_TOP25_MARGIN},
        {"metric": "OTA Commission %", "casaYano": round(ota_pct, 1), "sbMedian": SB_AVG_OTA_COMMISSION, "sbTop25": 12},
    ]

    # Repeat guests
    emails = [b.get("email", "").strip().lower() for b in bookings if b.get("email")]
    email_counts = defaultdict(int)
    for e in emails:
        if e:
            email_counts[e] += 1
    repeat_guests = sum(1 for c in email_counts.values() if c > 1)
    repeat_pct = round(repeat_guests / len(email_counts) * 100, 1) if email_counts else 0

    # ── Occupancy & RevPAR summary (realized only — past + current bookings) ──
    realized_nights = sum(b["nights"] for b in bookings if b["type"] in ("past", "current"))
    realized_gross = sum(b["gross"] for b in bookings if b["type"] in ("past", "current"))
    total_avail_nights = NUM_UNITS * days_since_launch
    total_occupancy = round(realized_nights / total_avail_nights * 100, 1) if total_avail_nights else 0
    blended_revpar = round(realized_gross / total_avail_nights) if total_avail_nights else 0

    # ── Actuals vs Model Projection + Forward Pace + Cumulative + Blended ──
    # The seasonal model's projection for each month (for comparison, even against closed months)
    model_projections = {}
    for i, name in enumerate(MONTH_NAMES_PF):
        mn = i + 1
        avail_nights = NUM_UNITS * calendar.monthrange(2026, mn)[1]
        proj_adr = round(baseline_adr * SB_ADR_SEASONAL[mn])
        proj_occ = min(round(baseline_occ * SB_OCC_SEASONAL[mn], 1), MAX_OCCUPANCY_PCT)
        proj_nights = round(avail_nights * proj_occ / 100)
        model_projections[name] = round(proj_adr * proj_nights)

    actuals_vs_pf = []
    cumulative_trajectory = []
    forward_pace = []
    actual_cumulative = 0
    pf_cumulative = 0

    for i, name in enumerate(MONTH_NAMES_PF):
        status = month_status[name]
        pf_gross_mo = pf_monthly[i]["gross"]
        model_gross = model_projections[name]

        booked = actual_rev.get(name)
        booked_gross = booked["gross"] if booked else 0

        if status == "closed" and booked_gross:
            variance = round(booked_gross - model_gross)
            variance_pct = round((booked_gross - model_gross) / model_gross * 100, 1) if model_gross else None
        else:
            variance = None
            variance_pct = None

        actuals_vs_pf.append({
            "month": name,
            "pfGross": model_gross,
            "actualGross": booked_gross if status == "closed" else 0,
            "bookedGross": booked_gross if status in ("current", "future") else 0,
            "variance": variance,
            "variancePct": variance_pct,
            "status": status,
        })

        pf_cumulative += pf_gross_mo
        if status in ("closed", "current"):
            actual_cumulative += booked_gross
        cumulative_trajectory.append({
            "month": name,
            "actualCumulative": round(actual_cumulative),
            "pfCumulative": round(pf_cumulative),
        })

        if status in ("current", "future"):
            pace_pct = round(booked_gross / pf_gross_mo * 100, 1) if pf_gross_mo and booked_gross else 0
            mn = i + 1
            avail_nights = NUM_UNITS * calendar.monthrange(2026, mn)[1]
            booked_nights = booked["nights"] if booked else 0
            booked_adr = round(booked_gross / booked_nights) if booked_nights else 0
            booked_revpar = round(booked_gross / avail_nights) if avail_nights else 0
            forward_pace.append({
                "month": name,
                "pfGross": pf_gross_mo,
                "bookedGross": round(booked_gross),
                "pacePct": pace_pct,
                "bookedAdr": booked_adr,
                "bookedRevpar": booked_revpar,
                "bookedNights": booked_nights,
                "availNights": avail_nights,
            })

    # Blended forecast = the dynamic pro forma itself (actuals + projections)
    blended_forecast = [{
        "month": m["month"], "gross": m["gross"], "netOwner": m["netOwner"],
        "adr": m["adr"], "occ": m["occ"], "opex": m["opex"],
        "noi": m["noi"], "source": m["source"],
    } for m in pf_monthly]

    blended_totals = {
        "gross": round(pf_gross),
        "netOwner": round(pf_net_owner),
        "opex": pf_opex,
        "mgmtFee": mgmt_fee,
        "noiBeforeFixed": round(pf_noi_before_fixed),
        "noiAfterKnown": round(pf_noi_after_known),
    }

    return {
        "generatedAt": datetime.now().isoformat(),
        "openingDate": OPENING_DATE.isoformat(),
        "daysSinceLaunch": days_since_launch,
        "numUnits": NUM_UNITS,
        "summary": {
            "totalBookings": total_bookings,
            "totalGross": round(total_gross),
            "totalToOwner": round(total_to_owner),
            "blendedAdr": round(blended_adr),
            "ownerMargin": round(owner_margin, 1),
            "otaPct": round(ota_pct, 1),
            "avgStay": round(avg_stay, 1),
            "avgLeadTime": round(avg_lead_time),
            "totalNights": total_nights,
            "totalExpenses": round(total_expense),
            "otaBookingPct": ota_booking_pct,
            "directBookings": direct_bookings,
            "repeatGuestPct": repeat_pct,
            "costPerTurn": cost_per_turn,
            "totalOccupancy": total_occupancy,
            "blendedRevPar": blended_revpar,
        },
        "monthlyData": monthly_data,
        "sourceData": source_data,
        "unitData": unit_data,
        "expenseCategories": expense_categories,
        "expenseMonthly": expense_monthly,
        "topVendors": top_vendors,
        "sbCompData": sb_comp,
        "actualsVsPf": actuals_vs_pf,
        "cumulativeTrajectory": cumulative_trajectory,
        "forwardPace": forward_pace,
        "blendedForecast": blended_forecast,
        "blendedTotals": blended_totals,
        "proForma": {
            "monthly": pf_monthly,
            "waterfall": pf_waterfall,
            "gross": pf_gross,
            "netOwner": pf_net_owner,
            "opex": pf_opex,
            "mgmtFee": mgmt_fee,
            "propertyTax": PROPERTY_TAX_ANNUAL,
            "insurance": INSURANCE_ANNUAL,
            "otherFixed": OTHER_FIXED_ANNUAL,
            "noiBeforeFixed": pf_noi_before_fixed,
            "noiAfterKnown": pf_noi_after_known,
            "avgOcc": round(pf_avg_occ, 1),
            "avgAdr": pf_avg_adr,
            "mgmtFeePct": MGMT_FEE_PCT,
            "baselineAdr": round(baseline_adr),
            "baselineOcc": round(baseline_occ, 1),
            "closedMonths": len(closed_metrics),
        },
        "forecastAccuracy": forecast_accuracy,
        "config": {
            "mgmtFeePct": MGMT_FEE_PCT,
            "propertyTaxAnnual": PROPERTY_TAX_ANNUAL,
            "insuranceAnnual": INSURANCE_ANNUAL,
            "sbMedianAdr": SB_MEDIAN_ADR,
            "sbTop25Adr": SB_TOP25_ADR,
        },
    }


def main():
    print("Casa Yano Dashboard Builder")
    print("=" * 40)
    print(f"Data directory: {DATA_DIR}")

    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True)
        print(f"Created {DATA_DIR} — drop your CSVs here and re-run.")
        return

    csvs = list(DATA_DIR.glob("*.csv"))
    if not csvs:
        print(f"No CSVs found in {DATA_DIR}. Drop your exports there and re-run.")
        return

    print(f"Found {len(csvs)} CSV files:")
    for f in csvs:
        print(f"  - {f.name}")

    print("\nParsing bookings...")
    bookings = load_bookings()
    print("Parsing expenses...")
    expenses = load_expenses()

    print("\nComputing metrics...")
    data = compute(bookings, expenses)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        f.write("// Auto-generated by build.py — do not edit manually\n")
        f.write(f"// Generated: {data['generatedAt']}\n")
        f.write(f"window.__DATA__ = {json.dumps(data, indent=2)};\n")

    print(f"\nWrote {OUTPUT}")
    print(f"  {data['summary']['totalBookings']} bookings, ${data['summary']['totalGross']:,} gross")
    print(f"  ADR: ${data['summary']['blendedAdr']}, Owner margin: {data['summary']['ownerMargin']}%")
    print(f"\nDeploy: cd {Path(__file__).parent} && vercel --prod")


if __name__ == "__main__":
    main()
