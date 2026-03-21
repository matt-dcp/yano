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

# Pro forma monthly projections — REVISED 2/22/26 based on 66 days of actuals
# Key calibrations from actual data:
#   - Jan ADR came in at $286 (vs $375 projected) — short winter stays, ramp-up pricing
#   - Feb ADR $397 — right on target, occupancy ~79%
#   - Mar already 62% booked at $392 ADR with 5 weeks lead time
#   - Blended owner margin: 89.4% (better than projected 83%)
#   - Cleaning: $105/turn actual (was $111 assumed)
#   - Forward ADR on books: $392 Mar, $477 Apr, $378 May, $479 Jun
# Methodology: Jan/Feb use actuals. Mar forward uses actual ADR where bookings exist,
# seasonal shape from original model, occupancy dialed to 70-80% (was 70-85%).
# OpEx = variable costs ONLY (cleaning, supplies, maint, marketing). Management fees
# are deducted separately in the waterfall as 10% of gross — NOT included here.
# Feb actual non-mgmt variable OpEx: ~$11K. Steady-state estimate: $7-11K/mo.
PF_MONTHLY = [
    {"month": "Jan", "adr": 286, "occ": 75, "gross": 40041, "netOwner": 35785, "opex": 11000, "noi": 24785, "bookings": 56},
    {"month": "Feb", "adr": 397, "occ": 79, "gross": 52466, "netOwner": 47423, "opex": 8500, "noi": 38923, "bookings": 53},
    {"month": "Mar", "adr": 392, "occ": 78, "gross": 56953, "netOwner": 50929, "opex": 8000, "noi": 42929, "bookings": 38},
    {"month": "Apr", "adr": 425, "occ": 75, "gross": 57375, "netOwner": 51295, "opex": 7500, "noi": 43795, "bookings": 35},
    {"month": "May", "adr": 420, "occ": 75, "gross": 58590, "netOwner": 52382, "opex": 7500, "noi": 44882, "bookings": 36},
    {"month": "Jun", "adr": 480, "occ": 80, "gross": 69120, "netOwner": 61775, "opex": 7000, "noi": 54775, "bookings": 40},
    {"month": "Jul", "adr": 500, "occ": 82, "gross": 76260, "netOwner": 68169, "opex": 7000, "noi": 61169, "bookings": 44},
    {"month": "Aug", "adr": 480, "occ": 80, "gross": 71424, "netOwner": 63853, "opex": 7000, "noi": 56853, "bookings": 42},
    {"month": "Sep", "adr": 375, "occ": 68, "gross": 45900, "netOwner": 41035, "opex": 7500, "noi": 33535, "bookings": 32},
    {"month": "Oct", "adr": 375, "occ": 65, "gross": 45338, "netOwner": 40532, "opex": 7500, "noi": 33032, "bookings": 30},
    {"month": "Nov", "adr": 385, "occ": 70, "gross": 48510, "netOwner": 43368, "opex": 7500, "noi": 35868, "bookings": 33},
    {"month": "Dec", "adr": 390, "occ": 75, "gross": 54405, "netOwner": 48638, "opex": 8000, "noi": 40638, "bookings": 37},
]

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
                                        "capex": 0, "maint": 0, "marketing": 0, "other": 0})
    cat_map = {"Cleaning": "cleaning", "Supplies": "supplies", "CapEx": "capex",
               "Maintenance": "maint", "Marketing": "marketing"}
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

    # ── Pro forma calculations ──
    pf_gross = sum(m["gross"] for m in PF_MONTHLY)
    pf_net_owner = sum(m["netOwner"] for m in PF_MONTHLY)
    pf_opex = sum(m["opex"] for m in PF_MONTHLY)
    pf_noi_before_fixed = pf_net_owner - pf_opex
    mgmt_fee = round(pf_gross * MGMT_FEE_PCT)
    pf_noi_after_known = pf_noi_before_fixed - mgmt_fee - PROPERTY_TAX_ANNUAL - INSURANCE_ANNUAL - OTHER_FIXED_ANNUAL
    pf_avg_occ = sum(m["occ"] for m in PF_MONTHLY) / 12
    pf_avg_adr = round(sum(m["adr"] for m in PF_MONTHLY) / 12)

    # Waterfall
    pf_total_ota = round(pf_gross * (ota_pct / 100))
    pf_total_tax = round(pf_gross * 0.12)  # ~12% TOT
    pf_total_proc = round(pf_gross * 0.025)
    pf_waterfall = [
        {"name": "Gross Revenue", "value": pf_gross, "type": "positive"},
        {"name": "OTA Commissions", "value": -pf_total_ota, "type": "negative"},
        {"name": "Taxes (TOT)", "value": -pf_total_tax, "type": "negative"},
        {"name": "Processing", "value": -pf_total_proc, "type": "negative"},
        {"name": "Net to Owner", "value": pf_net_owner, "type": "subtotal"},
        {"name": "Cleaning", "value": -round(pf_opex * 0.83), "type": "opex"},
        {"name": "Supplies/Maint", "value": -round(pf_opex * 0.14), "type": "opex"},
        {"name": "Other OpEx", "value": -round(pf_opex * 0.03), "type": "opex"},
        {"name": "Mgmt Fee (10%)", "value": -mgmt_fee, "type": "mgmt"},
        {"name": "Property Tax", "value": -PROPERTY_TAX_ANNUAL, "type": "opex"},
        {"name": "Insurance", "value": -INSURANCE_ANNUAL, "type": "opex"},
        {"name": "Other Fixed (6 items)", "value": -OTHER_FIXED_ANNUAL, "type": "opex"},
        {"name": "NOI (excl. remaining TBD)", "value": pf_noi_after_known, "type": "total"},
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

    # ── Actuals vs Pro Forma + Forward Pace + Cumulative + Blended ──
    # Build lookup of actual monthly data keyed by PF-style month name
    actual_lookup = {}  # "Jan" → {gross, toOwner, bookings, nights, occ, adr}
    for md in monthly_data:
        # Convert "Jan '26" → "Jan", "Feb '26" → "Feb", "Dec '25" → skip (opening month, not in PF)
        mk = md["month"]
        parts = mk.split(" '")
        if len(parts) == 2:
            month_abbr = parts[0]
            yr = int(parts[1]) + 2000
            # PF covers Jan-Dec 2026. Dec '25 is NOT in PF.
            if yr == 2026:
                actual_lookup[month_abbr] = md

    # Determine which months are closed vs current vs future
    current_month_abbr = today.strftime("%b")
    current_year = today.year

    actuals_vs_pf = []
    cumulative_trajectory = []
    forward_pace = []
    blended_forecast = []
    actual_cumulative = 0
    pf_cumulative = 0
    blended_gross_total = 0
    blended_net_total = 0

    for pf_entry in PF_MONTHLY:
        pf_month = pf_entry["month"]  # "Jan", "Feb", etc.
        pf_gross_mo = pf_entry["gross"]
        pf_net_mo = pf_entry["netOwner"]

        # Determine status
        month_num = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(pf_month) + 1
        month_end = date(2026, month_num, calendar.monthrange(2026, month_num)[1])
        month_start = date(2026, month_num, 1)

        if month_end < today:
            status = "closed"
        elif month_start <= today <= month_end:
            status = "current"
        else:
            status = "future"

        actual = actual_lookup.get(pf_month)
        actual_gross_mo = actual["gross"] if actual else 0
        actual_net_mo = actual["toOwner"] if actual else 0

        # Variance (only meaningful for closed months)
        variance = round(actual_gross_mo - pf_gross_mo) if status == "closed" else None
        variance_pct = round((actual_gross_mo - pf_gross_mo) / pf_gross_mo * 100, 1) if status == "closed" and pf_gross_mo else None

        actuals_vs_pf.append({
            "month": pf_month,
            "pfGross": pf_gross_mo,
            "actualGross": actual_gross_mo if status == "closed" else 0,
            "bookedGross": actual_gross_mo if status in ("current", "future") else 0,
            "variance": variance,
            "variancePct": variance_pct,
            "status": status,
        })

        # Cumulative trajectory
        pf_cumulative += pf_gross_mo
        if status == "closed":
            actual_cumulative += actual_gross_mo
        elif status == "current":
            actual_cumulative += actual_gross_mo  # partial month, show what we have
        cumulative_trajectory.append({
            "month": pf_month,
            "actualCumulative": round(actual_cumulative),
            "pfCumulative": round(pf_cumulative),
        })

        # Forward pace (future + current months only)
        if status in ("current", "future"):
            pace_pct = round(actual_gross_mo / pf_gross_mo * 100, 1) if pf_gross_mo else 0
            forward_pace.append({
                "month": pf_month,
                "pfGross": pf_gross_mo,
                "bookedGross": round(actual_gross_mo),
                "pacePct": pace_pct,
            })

        # Blended forecast: actuals for closed, PF for future
        if status == "closed" and actual:
            blended_forecast.append({
                "month": pf_month,
                "gross": actual["gross"],
                "netOwner": actual["toOwner"],
                "adr": actual["adr"],
                "occ": actual.get("occupancy", pf_entry["occ"]),
                "opex": pf_entry["opex"],  # use PF opex (actuals don't have monthly opex breakdown yet)
                "noi": actual["toOwner"] - pf_entry["opex"],
                "source": "actual",
            })
            blended_gross_total += actual["gross"]
            blended_net_total += actual["toOwner"]
        else:
            blended_forecast.append({
                "month": pf_month,
                "gross": pf_gross_mo,
                "netOwner": pf_net_mo,
                "adr": pf_entry["adr"],
                "occ": pf_entry["occ"],
                "opex": pf_entry["opex"],
                "noi": pf_entry["noi"],
                "source": "projected",
            })
            blended_gross_total += pf_gross_mo
            blended_net_total += pf_net_mo

    # Blended totals
    blended_opex = sum(bf["opex"] for bf in blended_forecast)
    blended_noi_before_fixed = blended_net_total - blended_opex
    blended_mgmt = round(blended_gross_total * MGMT_FEE_PCT)
    blended_noi_after_known = blended_noi_before_fixed - blended_mgmt - PROPERTY_TAX_ANNUAL - INSURANCE_ANNUAL - OTHER_FIXED_ANNUAL

    blended_totals = {
        "gross": round(blended_gross_total),
        "netOwner": round(blended_net_total),
        "opex": blended_opex,
        "mgmtFee": blended_mgmt,
        "noiBeforeFixed": round(blended_noi_before_fixed),
        "noiAfterKnown": round(blended_noi_after_known),
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
            "monthly": PF_MONTHLY,
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
        },
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
