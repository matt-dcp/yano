#!/usr/bin/env python3
"""Build Casa Yano lender package spreadsheet from data.js + QBO financials"""

import json, calendar
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter

# Load dashboard data
with open(Path(__file__).parent / "public" / "data.js") as f:
    raw = f.read()
    D = json.loads(raw.split("window.__DATA__ = ")[1].rstrip(";\n"))

PF = D["proForma"]
pf_m = PF["monthly"]
exp_m = D["expenseMonthly"]
fwd = D["forwardPace"]
fa = D["forecastAccuracy"]

wb = Workbook()

# ── Styles ──
DARK = PatternFill("solid", fgColor="2D2D2D")
GOLD_FILL = PatternFill("solid", fgColor="C5A55A")
LIGHT_GRAY = PatternFill("solid", fgColor="F5F5F5")
GREEN_FILL = PatternFill("solid", fgColor="E8F5E9")
BLUE_FILL = PatternFill("solid", fgColor="E3F2FD")
YELLOW_FILL = PatternFill("solid", fgColor="FFFDE7")
LIGHT_GOLD = PatternFill("solid", fgColor="F5ECD7")

HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=11)
GOLD_FONT = Font(name="Arial", bold=True, color="C5A55A", size=11)
TITLE_FONT = Font(name="Arial", bold=True, size=14, color="2D2D2D")
SECTION_FONT = Font(name="Arial", bold=True, size=12, color="2D2D2D")
BODY = Font(name="Arial", size=10, color="333333")
BOLD = Font(name="Arial", bold=True, size=10, color="333333")
BLUE_INPUT = Font(name="Arial", size=10, color="0000FF")
GREEN_LINK = Font(name="Arial", size=10, color="008000")
NOTE_FONT = Font(name="Arial", size=9, color="999999")
MONEY = '$#,##0;($#,##0);"-"'
PCT = '0.0%'
NUM = '#,##0'
THIN_B = Border(bottom=Side(style="thin", color="DDDDDD"))
THICK_B = Border(bottom=Side(style="medium", color="2D2D2D"))

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def hdr_row(ws, row, cols, fill=DARK, font=HEADER_FONT):
    for c in range(1, cols+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def alt_fill(ws, row, cols):
    if row % 2 == 0:
        for c in range(1, cols+1): ws.cell(row, c).fill = LIGHT_GRAY

def write_item(ws, row, label, val, fmt=None, bold=False, indent=False, font=None, col_label=1, col_val=2):
    lbl = f"  {label}" if indent else label
    ws.cell(row, col_label, lbl).font = BOLD if bold else BODY
    c = ws.cell(row, col_val, val)
    c.font = font or (BOLD if bold else BODY)
    if fmt: c.number_format = fmt
    ws.cell(row, col_label).border = THIN_B
    ws.cell(row, col_val).border = THIN_B
    return row + 1

def section_hdr(ws, row, title, cols=2):
    ws.cell(row, 1, title).font = SECTION_FONT
    for c in range(1, cols+1): ws.cell(row, c).border = THICK_B
    return row + 1

# QBO data (hardcoded from extracted financials)
QBO_BS_2026 = {
    "cash": 1457,
    "fixed_assets": {
        "acquisition_fee": 49500, "appliances": 1810.81, "buildings": 1890016.53,
        "cost_seg": 5920, "fundraising": 11250, "ff_e": 73760.68,
        "land": 596847.33, "landscaping": 821.86, "photography": 2175,
        "rehab_hard": 1405644.37, "rehab_soft": 159844.11,
        "rehab_total": 1565488.48, "total": 4197590.69,
    },
    "total_assets": 4199047.69,
    "current_liab": 2063.95,
    "lt_debt": {"cdrbc": 1000000, "gft_ira": 500000, "total": 1500000},
    "total_liab": 1502063.95,
    "retained_earnings": -343121.08,
    "net_income_ytd": 9280.01,
    "total_equity": -333841.07,
}

QBO_PL_2026 = {
    "rent": 170225.30,
    "expenses": {
        "advertising": 2410, "commissions": 434.95, "guest_relations": 539.50,
        "mgmt_fee": 17365.29, "landscaping": 450,
        "cleaning": 23141.28, "fire_safety": 450, "general_repairs": 1887, "pest_control": 210,
        "repairs_total": 25688.28,
        "supplies": 9477.71,
        "city_county_tax": 15798.09, "property_tax": 13339.62, "state_tax": 1612.76,
        "taxes_total": 30750.47,
        "disposal": 50, "electricity": 564.30, "internet": 1163.25, "water": 444.24,
        "utilities_total": 2221.79,
        "total": 89337.99,
    },
    "noi": 80887.31,
    "bank_charges": 357.30,
    "mortgage_interest": 71250,
    "net_income": 9280.01,
}


# ════════════════════════════════════════════════════════
# TAB 1: Executive Summary
# ════════════════════════════════════════════════════════
ws1 = wb.active
ws1.title = "Executive Summary"
ws1.sheet_properties.tabColor = "C5A55A"
ws1.column_dimensions["A"].width = 30
ws1.column_dimensions["B"].width = 22
ws1.column_dimensions["C"].width = 5
ws1.column_dimensions["D"].width = 30
ws1.column_dimensions["E"].width = 22

r = 1
ws1.cell(r, 1, "Casa Yano — Lender Package").font = Font(name="Arial", bold=True, size=18, color="2D2D2D")
ws1.merge_cells("A1:E1")
r = 2
ws1.cell(r, 1, "210 W Yanonali St, Santa Barbara, CA 93101").font = Font(name="Arial", size=11, color="666666")
ws1.merge_cells("A2:E2")
r = 3
ws1.cell(r, 1, f"Prepared {D['generatedAt'][:10]}").font = NOTE_FONT
ws1.merge_cells("A3:E3")

r = 5
r = section_hdr(ws1, r, "PROPERTY DETAILS")
props = [
    ("Property Type", "Short-Term Rental (STR)"),
    ("Units", "6"),
    ("Location", "Santa Barbara, CA"),
    ("Opening Date", "December 18, 2025"),
    ("Days Operating", str(D["daysSinceLaunch"])),
    ("Management", "ZenStay Inc (third-party, 10% of gross)"),
]
for label, val in props:
    r = write_item(ws1, r, label, val)

r += 1
r_ytd_start = r
r = section_hdr(ws1, r, "YTD PERFORMANCE (QBO — Cash Basis)")
section_hdr(ws1, r_ytd_start, "FULL-YEAR PRO FORMA", cols=2)
ws1.cell(r_ytd_start, 4, "FULL-YEAR PRO FORMA").font = SECTION_FONT
ws1.cell(r_ytd_start, 4).border = THICK_B
ws1.cell(r_ytd_start, 5).border = THICK_B

ytd_items = [
    ("Period", "Jan 1 – Apr 14, 2026", None),
    ("Rental Income", QBO_PL_2026["rent"], MONEY),
    ("Total Operating Expenses", QBO_PL_2026["expenses"]["total"], MONEY),
    ("Net Operating Income", QBO_PL_2026["noi"], MONEY),
]
pf_items = [
    ("Projection Basis", f"{PF['closedMonths']} months actuals + seasonal model", None),
    ("Gross Revenue", PF["gross"], MONEY),
    ("Net to Owner", PF["netOwner"], MONEY),
    ("Total OpEx + Fixed", PF["opex"] + PF["mgmtFee"] + PF["propertyTax"] + PF["insurance"] + PF["otherFixed"], MONEY),
    ("NOI (After Known Fixed)", PF["noiAfterKnown"], MONEY),
    ("Avg ADR (Blended)", PF["avgAdr"], MONEY),
    ("Avg Occupancy (Blended)", PF["avgOcc"] / 100, PCT),
]

start_r = r
for label, val, fmt in ytd_items:
    r = write_item(ws1, r, label, val, fmt, bold=(label == "Net Operating Income"))
r_ytd_end = r

r = start_r
for label, val, fmt in pf_items:
    write_item(ws1, r, label, val, fmt, bold=(label == "NOI (After Known Fixed)"), col_label=4, col_val=5)
    r += 1

r = max(r_ytd_end, r) + 1
r = section_hdr(ws1, r, "KEY HIGHLIGHTS", cols=5)
highlights = [
    f"Total project basis: ${QBO_BS_2026['fixed_assets']['total']:,.0f} (per QBO balance sheet)",
    f"Existing debt: ${QBO_BS_2026['lt_debt']['total']:,.0f} — seeking refinance",
    f"Occupancy trending from 75% (Jan) to 88% (Mar) — strong ramp trajectory",
    f"April booked at ${pf_m[3]['gross']:,} gross — highest month to date",
    f"Owner margin of {D['summary']['ownerMargin']}% — efficient operations with low OTA commission rates",
    f"QBO YTD NOI of ${QBO_PL_2026['noi']:,.0f} in first 3.5 months of operations",
]
for h in highlights:
    ws1.cell(r, 1, f"•  {h}").font = BODY
    ws1.merge_cells(f"A{r}:E{r}")
    r += 1

ws1.freeze_panes = "A5"


# ════════════════════════════════════════════════════════
# TAB 2: Project History
# ════════════════════════════════════════════════════════
ws2 = wb.create_sheet("Project History")
ws2.sheet_properties.tabColor = "795548"
ws2.column_dimensions["A"].width = 32
ws2.column_dimensions["B"].width = 22
ws2.column_dimensions["C"].width = 5
ws2.column_dimensions["D"].width = 32
ws2.column_dimensions["E"].width = 22

r = 1
ws2.cell(r, 1, "Casa Yano — Project History & Renovation").font = Font(name="Arial", bold=True, size=18, color="2D2D2D")
ws2.merge_cells("A1:E1")
r = 2
ws2.cell(r, 1, "Source: QuickBooks Online balance sheet + project records").font = NOTE_FONT
ws2.merge_cells("A2:E2")

r = 4
r = section_hdr(ws2, r, "ACQUISITION")
for label, val, fmt in [("Purchase Price", 2475000, MONEY), ("Close Date", "March 2024", None)]:
    r = write_item(ws2, r, label, val, fmt)

r += 1
r = section_hdr(ws2, r, "RENOVATION")
reno_items = [
    ("Total Construction Cost (QBO)", round(QBO_BS_2026["fixed_assets"]["rehab_total"]), MONEY),
    ("Hard Costs", round(QBO_BS_2026["fixed_assets"]["rehab_hard"]), MONEY),
    ("Soft Costs", round(QBO_BS_2026["fixed_assets"]["rehab_soft"]), MONEY),
    ("Renovation Start", "October 2024", None),
    ("Renovation Complete", "November 2025", None),
    ("Duration", "13 months", None),
    ("Scope", "Full gut renovation to studs", None),
]
for label, val, fmt in reno_items:
    r = write_item(ws2, r, label, val, fmt, indent=label in ("Hard Costs", "Soft Costs"))

r += 1
r = section_hdr(ws2, r, "SCOPE OF WORK", cols=5)
scope = [
    ("Structural", "Rebuilt foundation including underpinning with pylons"),
    ("Framing & Envelope", "New framing, new windows, new roof, new stucco"),
    ("Mechanical", "All new plumbing, all new electrical"),
    ("HVAC", "New mini splits in each unit"),
    ("Insulation & Walls", "All new insulation, all new drywall"),
    ("Interiors", "All new flooring, lighting, kitchens, bathrooms, and finishes"),
    ("Exterior", "New hardscape and landscape throughout the property"),
]
for label, desc in scope:
    ws2.cell(r, 1, label).font = BOLD
    ws2.cell(r, 2, desc).font = BODY
    ws2.merge_cells(f"B{r}:E{r}")
    ws2.cell(r, 1).border = THIN_B
    ws2.cell(r, 2).border = THIN_B
    r += 1

r += 1
r = section_hdr(ws2, r, "TOTAL PROJECT COST (per QBO Balance Sheet)")
cost_start = r
cost_items = [
    ("Land", round(QBO_BS_2026["fixed_assets"]["land"]), MONEY),
    ("Buildings", round(QBO_BS_2026["fixed_assets"]["buildings"]), MONEY),
    ("Rehab Costs — Hard", round(QBO_BS_2026["fixed_assets"]["rehab_hard"]), MONEY),
    ("Rehab Costs — Soft", round(QBO_BS_2026["fixed_assets"]["rehab_soft"]), MONEY),
    ("FF&E / Furniture & Fixtures", round(QBO_BS_2026["fixed_assets"]["ff_e"]), MONEY),
    ("Other (Acq Fee, Fundraising, Cost Seg, etc.)", round(49500 + 11250 + 5920 + 1810.81 + 821.86 + 2175), MONEY),
]
for label, val, fmt in cost_items:
    r = write_item(ws2, r, label, val, fmt)
# Total
ws2.cell(r, 1, "Total Fixed Assets").font = Font(name="Arial", bold=True, size=11, color="2D2D2D")
ws2.cell(r, 2).value = f"=SUM(B{cost_start}:B{r-1})"
ws2.cell(r, 2).font = Font(name="Arial", bold=True, size=11, color="2D2D2D")
ws2.cell(r, 2).number_format = MONEY
ws2.cell(r, 1).border = Border(top=Side(style="medium", color="2D2D2D"), bottom=Side(style="medium", color="2D2D2D"))
ws2.cell(r, 2).border = Border(top=Side(style="medium", color="2D2D2D"), bottom=Side(style="medium", color="2D2D2D"))
r_total_assets = r
r += 2

r = section_hdr(ws2, r, "EXISTING DEBT")
for label, val, fmt in [
    ("CDRBC, LLC", QBO_BS_2026["lt_debt"]["cdrbc"], MONEY),
    ("GFT IRA, LLC", QBO_BS_2026["lt_debt"]["gft_ira"], MONEY),
    ("Total Existing Debt", QBO_BS_2026["lt_debt"]["total"], MONEY),
]:
    r = write_item(ws2, r, label, val, fmt, bold=(label.startswith("Total")))

r += 1
r = section_hdr(ws2, r, "VALUE CREATION")
val_start = r
for label, val, fmt in [
    ("Projected NOI (2026)", PF["noiAfterKnown"], MONEY),
    ("Cap Rate Applied", 0.06, PCT),
]:
    r = write_item(ws2, r, label, val, fmt)
ws2.cell(r, 1, "Implied Value").font = BOLD
ws2.cell(r, 2).value = f"=B{val_start}/B{val_start+1}"
ws2.cell(r, 2).font = BOLD
ws2.cell(r, 2).number_format = MONEY
ws2.cell(r, 1).border = THIN_B
ws2.cell(r, 2).border = THIN_B
r += 1
ws2.cell(r, 1, "Total Basis (per QBO)").font = BODY
ws2.cell(r, 2).value = f"=B{r_total_assets}"
ws2.cell(r, 2).font = GREEN_LINK
ws2.cell(r, 2).number_format = MONEY
ws2.cell(r, 1).border = THIN_B
ws2.cell(r, 2).border = THIN_B
r += 1
ws2.cell(r, 1, "Value Created").font = Font(name="Arial", bold=True, size=11, color="4CAF50")
ws2.cell(r, 2).value = f"=B{r-2}-B{r-1}"
ws2.cell(r, 2).font = Font(name="Arial", bold=True, size=11, color="4CAF50")
ws2.cell(r, 2).number_format = MONEY
ws2.cell(r, 1).border = THIN_B
ws2.cell(r, 2).border = THIN_B
r += 1
ws2.cell(r, 1, "Return on Cost").font = BOLD
ws2.cell(r, 2).value = f"=B{val_start}/B{r-2}"
ws2.cell(r, 2).font = BOLD
ws2.cell(r, 2).number_format = PCT
ws2.cell(r, 1).border = THIN_B
ws2.cell(r, 2).border = THIN_B

r += 2
r = section_hdr(ws2, r, "TIMELINE", cols=5)
timeline = [
    ("Mar 2024", "Property acquired"),
    ("Mar – Sep 2024", "Planning, permitting, design"),
    ("Oct 2024", "Construction begins — full gut renovation"),
    ("Nov 2025", "Construction complete — certificate of occupancy"),
    ("Dec 18, 2025", "First guest booking — STR operations commence"),
    ("Jan – Mar 2026", "First full quarter of operations — strong ramp"),
    ("Apr 2026", "Highest-grossing month to date"),
]
for date, event in timeline:
    ws2.cell(r, 1, date).font = BOLD
    ws2.cell(r, 2, event).font = BODY
    ws2.merge_cells(f"B{r}:E{r}")
    ws2.cell(r, 1).border = THIN_B
    ws2.cell(r, 2).border = THIN_B
    r += 1

ws2.freeze_panes = "A4"


# ════════════════════════════════════════════════════════
# TAB 3: QBO P&L (2026 YTD)
# ════════════════════════════════════════════════════════
ws3 = wb.create_sheet("QBO P&L (2026 YTD)")
ws3.sheet_properties.tabColor = "2D8B2D"
ws3.column_dimensions["A"].width = 36
ws3.column_dimensions["B"].width = 18
ws3.column_dimensions["C"].width = 18

r = 1
ws3.cell(r, 1, "DCP Wealth Fund, LLC — Yanonali").font = TITLE_FONT
ws3.merge_cells("A1:C1")
r = 2
ws3.cell(r, 1, "Profit and Loss: January 1 – April 14, 2026  |  Cash Basis").font = Font(name="Arial", size=11, color="666666")
ws3.merge_cells("A2:C2")
r = 3
ws3.cell(r, 1, "Source: QuickBooks Online, exported April 14, 2026").font = NOTE_FONT
ws3.merge_cells("A3:C3")

r = 5
hdr_row(ws3, r, 2)
ws3.cell(r, 1, "").font = HEADER_FONT
ws3.cell(r, 2, "Amount").font = HEADER_FONT
r += 1

# Income
ws3.cell(r, 1, "INCOME").font = BOLD
for c in range(1, 3): ws3.cell(r, c).fill = LIGHT_GRAY
r += 1
r = write_item(ws3, r, "Rent", 170225.30, MONEY, bold=True)
r = write_item(ws3, r, "Gross Profit", 170225.30, MONEY, bold=True)

r += 1
ws3.cell(r, 1, "EXPENSES").font = BOLD
for c in range(1, 3): ws3.cell(r, c).fill = LIGHT_GRAY
r += 1

pl_expenses = [
    ("Advertising & Marketing", 2410, False),
    ("Commissions Expense", 434.95, False),
    ("Guest Relations", 539.50, False),
    ("Hospitality Management Fee", 17365.29, False),
    ("Landscaping", 450, False),
    ("Repairs & Maintenance", None, True),
    ("  Cleaning Expenses", 23141.28, False),
    ("  Fire Safety", 450, False),
    ("  General Repairs", 1887, False),
    ("  Pest Control", 210, False),
    ("  Total Repairs & Maintenance", 25688.28, True),
    ("Supplies", None, True),
    ("  Supplies", 6140.12, False),
    ("  Supplies & Materials", 3337.59, False),
    ("  Total Supplies", 9477.71, True),
    ("Taxes Paid", None, True),
    ("  City & County Tax", 15798.09, False),
    ("  Property Taxes", 13339.62, False),
    ("  State Tax", 1612.76, False),
    ("  Total Taxes Paid", 30750.47, True),
    ("Utilities", None, True),
    ("  Disposal & Waste", 50, False),
    ("  Electricity", 564.30, False),
    ("  Internet & TV", 1163.25, False),
    ("  Water & Sewer", 444.24, False),
    ("  Total Utilities", 2221.79, True),
]

for label, val, is_bold in pl_expenses:
    if val is None:
        ws3.cell(r, 1, label).font = BOLD
        r += 1
        continue
    ws3.cell(r, 1, label).font = BOLD if is_bold else BODY
    ws3.cell(r, 2, val).number_format = MONEY
    ws3.cell(r, 2).font = BOLD if is_bold else BODY
    ws3.cell(r, 1).border = THIN_B
    ws3.cell(r, 2).border = THIN_B
    r += 1

# Total expenses
ws3.cell(r, 1, "Total Expenses").font = Font(name="Arial", bold=True, size=11, color="E53935")
ws3.cell(r, 2, 89337.99).number_format = MONEY
ws3.cell(r, 2).font = Font(name="Arial", bold=True, size=11, color="E53935")
for c in range(1, 3): ws3.cell(r, c).border = THICK_B
r += 2

# NOI
ws3.cell(r, 1, "Net Operating Income").font = Font(name="Arial", bold=True, size=12, color="2D8B2D")
ws3.cell(r, 2, 80887.31).number_format = MONEY
ws3.cell(r, 2).font = Font(name="Arial", bold=True, size=12, color="2D8B2D")
for c in range(1, 3): ws3.cell(r, c).fill = GREEN_FILL

ws3.freeze_panes = "A5"


# ════════════════════════════════════════════════════════
# TAB 4: QBO Balance Sheet
# ════════════════════════════════════════════════════════
ws4 = wb.create_sheet("QBO Balance Sheet")
ws4.sheet_properties.tabColor = "1565C0"
ws4.column_dimensions["A"].width = 40
ws4.column_dimensions["B"].width = 20
ws4.column_dimensions["C"].width = 20

r = 1
ws4.cell(r, 1, "DCP Wealth Fund, LLC — Yanonali").font = TITLE_FONT
ws4.merge_cells("A1:C1")
r = 2
ws4.cell(r, 1, "Balance Sheet as of April 14, 2026  |  Cash Basis").font = Font(name="Arial", size=11, color="666666")
ws4.merge_cells("A2:C2")
r = 3
ws4.cell(r, 1, "Source: QuickBooks Online, exported April 14, 2026").font = NOTE_FONT
ws4.merge_cells("A3:C3")

r = 5
hdr_row(ws4, r, 2)
ws4.cell(r, 1, "").font = HEADER_FONT
ws4.cell(r, 2, "Amount").font = HEADER_FONT
r += 1

# ASSETS
ws4.cell(r, 1, "ASSETS").font = BOLD
for c in range(1, 3): ws4.cell(r, c).fill = LIGHT_GRAY
r += 1
r = write_item(ws4, r, "Current Assets — Bank Accounts", 1457, MONEY)

r += 1
ws4.cell(r, 1, "Fixed Assets").font = BOLD
r += 1
fixed_lines = [
    ("Land", 596847.33), ("Buildings", 1890016.53),
    ("Acquisition Fee", 49500), ("Fundraising Fee", 11250), ("Cost Segregation", 5920),
    ("Furniture & Fixtures", 73760.68), ("Appliances", 1810.81),
    ("Landscaping", 821.86), ("Photography", 2175),
]
fa_start = r
for label, val in fixed_lines:
    r = write_item(ws4, r, label, round(val), MONEY, indent=True)

# Rehab costs
ws4.cell(r, 1, "  Rehab Costs — Hard").font = BOLD
ws4.cell(r, 2, round(QBO_BS_2026["fixed_assets"]["rehab_hard"])).number_format = MONEY
ws4.cell(r, 2).font = BOLD
ws4.cell(r, 1).border = THIN_B
ws4.cell(r, 2).border = THIN_B
r += 1
rehab_hard_detail = [
    ("    General Hard Costs", 201886.43), ("    Contractors/Labor", 1026420.32), ("    Materials", 177337.62),
]
for label, val in rehab_hard_detail:
    ws4.cell(r, 1, label).font = NOTE_FONT
    ws4.cell(r, 2, round(val)).number_format = MONEY
    ws4.cell(r, 2).font = NOTE_FONT
    ws4.cell(r, 1).border = THIN_B
    ws4.cell(r, 2).border = THIN_B
    r += 1

ws4.cell(r, 1, "  Rehab Costs — Soft").font = BOLD
ws4.cell(r, 2, round(QBO_BS_2026["fixed_assets"]["rehab_soft"])).number_format = MONEY
ws4.cell(r, 2).font = BOLD
ws4.cell(r, 1).border = THIN_B
ws4.cell(r, 2).border = THIN_B
r += 1
rehab_soft_detail = [
    ("    Architectural/Planning", 25391.16), ("    Inspection Fees", 4135),
    ("    Legal & Professional", 1725), ("    Permit Fees", 16663.46),
    ("    Rehab Management", 59884.49), ("    Survey", 895), ("    Tenant Relocation", 51150),
]
for label, val in rehab_soft_detail:
    ws4.cell(r, 1, label).font = NOTE_FONT
    ws4.cell(r, 2, round(val)).number_format = MONEY
    ws4.cell(r, 2).font = NOTE_FONT
    ws4.cell(r, 1).border = THIN_B
    ws4.cell(r, 2).border = THIN_B
    r += 1

# Total fixed
ws4.cell(r, 1, "Total Fixed Assets").font = Font(name="Arial", bold=True, size=11, color="2D2D2D")
ws4.cell(r, 2, round(QBO_BS_2026["fixed_assets"]["total"])).number_format = MONEY
ws4.cell(r, 2).font = Font(name="Arial", bold=True, size=11, color="2D2D2D")
for c in range(1, 3): ws4.cell(r, c).border = THICK_B
r += 1

# Total assets
ws4.cell(r, 1, "TOTAL ASSETS").font = Font(name="Arial", bold=True, size=12, color="2D2D2D")
ws4.cell(r, 2, round(QBO_BS_2026["total_assets"])).number_format = MONEY
ws4.cell(r, 2).font = Font(name="Arial", bold=True, size=12, color="2D2D2D")
for c in range(1, 3): ws4.cell(r, c).fill = LIGHT_GOLD
r += 2

# LIABILITIES
ws4.cell(r, 1, "LIABILITIES").font = BOLD
for c in range(1, 3): ws4.cell(r, c).fill = LIGHT_GRAY
r += 1
r = write_item(ws4, r, "Current Liabilities", round(QBO_BS_2026["current_liab"]), MONEY, indent=True)
ws4.cell(r, 1, "Long-term Liabilities").font = BOLD
r += 1
r = write_item(ws4, r, "CDRBC, LLC", 1000000, MONEY, indent=True)
r = write_item(ws4, r, "GFT IRA, LLC", 500000, MONEY, indent=True)
r = write_item(ws4, r, "Total Long-term Debt", 1500000, MONEY, bold=True)
ws4.cell(r, 1, "TOTAL LIABILITIES").font = Font(name="Arial", bold=True, size=11, color="2D2D2D")
ws4.cell(r, 2, round(QBO_BS_2026["total_liab"])).number_format = MONEY
ws4.cell(r, 2).font = Font(name="Arial", bold=True, size=11, color="2D2D2D")
for c in range(1, 3): ws4.cell(r, c).border = THICK_B
r += 2

# EQUITY
ws4.cell(r, 1, "EQUITY").font = BOLD
for c in range(1, 3): ws4.cell(r, c).fill = LIGHT_GRAY
r += 1
r = write_item(ws4, r, "Retained Earnings", round(QBO_BS_2026["retained_earnings"]), MONEY)
r = write_item(ws4, r, "Net Income (YTD 2026)", round(QBO_BS_2026["net_income_ytd"]), MONEY)
r = write_item(ws4, r, "Total Equity", round(QBO_BS_2026["total_equity"]), MONEY, bold=True)

ws4.freeze_panes = "A5"


# ════════════════════════════════════════════════════════
# TAB 5: Operating Detail (PMS data)
# ════════════════════════════════════════════════════════
ws5 = wb.create_sheet("Operating Detail")
ws5.sheet_properties.tabColor = "C5A55A"
ws5.column_dimensions["A"].width = 22
for c in range(2, 16): ws5.column_dimensions[get_column_letter(c)].width = 12

r = 1
ws5.cell(r, 1, "Casa Yano — Monthly Operating Detail (2026)").font = TITLE_FONT
ws5.merge_cells("A1:M1")
r = 2
ws5.cell(r, 1, "Source: Property Management System booking data").font = NOTE_FONT
ws5.merge_cells("A2:M2")
r = 4

# Source row
ws5.cell(r, 1, "Status").font = BOLD
for i, m in enumerate(pf_m):
    cell = ws5.cell(r, i+2, m["source"].upper())
    cell.font = Font(name="Arial", bold=True, size=9, color="FFFFFF")
    cell.alignment = Alignment(horizontal="center")
    cell.fill = PatternFill("solid", fgColor="4CAF50" if m["source"] == "actual" else "2196F3" if m["source"] == "booked" else "9E9E9E")
r = 5

headers = [""] + MONTHS + ["Full Year"]
for i, h in enumerate(headers):
    ws5.cell(r, i+1, h)
hdr_row(ws5, r, 14)
ws5.cell(r, 1).alignment = Alignment(horizontal="left")
r += 1

# Compute nights/avail
rev_data = []
for i, m in enumerate(pf_m):
    mn = i + 1
    days = calendar.monthrange(2026, mn)[1]
    avail = 6 * days
    nights = round(avail * m["occ"] / 100)
    revpar = round(m["gross"] / avail) if avail else 0
    rev_data.append({"bookings": m["bookings"], "nights": nights, "avail": avail,
                      "occ": m["occ"], "adr": m["adr"], "revpar": revpar,
                      "gross": m["gross"], "net": m["netOwner"]})

rev_rows = [
    ("Bookings", [d["bookings"] for d in rev_data], NUM),
    ("Nights Sold", [d["nights"] for d in rev_data], NUM),
    ("Available Nights", [d["avail"] for d in rev_data], NUM),
    ("Occupancy", [d["occ"] / 100 for d in rev_data], PCT),
    ("ADR", [d["adr"] for d in rev_data], MONEY),
    ("RevPAR", [d["revpar"] for d in rev_data], MONEY),
    ("Gross Revenue", [d["gross"] for d in rev_data], MONEY),
    ("Net to Owner", [d["net"] for d in rev_data], MONEY),
]

for label, vals, fmt in rev_rows:
    is_bold = label in ("Gross Revenue", "Net to Owner")
    ws5.cell(r, 1, label).font = BOLD if is_bold else BODY
    for i, v in enumerate(vals):
        ws5.cell(r, i+2, v).number_format = fmt
        ws5.cell(r, i+2).font = BOLD if is_bold else BODY
        ws5.cell(r, i+2).alignment = Alignment(horizontal="right")
    if fmt in (MONEY, NUM):
        ws5.cell(r, 14, f"=SUM(B{r}:M{r})").number_format = fmt
    elif fmt == PCT:
        ws5.cell(r, 14, f"=AVERAGE(B{r}:M{r})").number_format = fmt
    ws5.cell(r, 14).font = BOLD
    alt_fill(ws5, r, 14)
    r += 1

ws5.freeze_panes = "B6"


# ════════════════════════════════════════════════════════
# TAB 6: Forward Bookings
# ════════════════════════════════════════════════════════
ws6 = wb.create_sheet("Forward Bookings")
ws6.sheet_properties.tabColor = "2196F3"
ws6.column_dimensions["A"].width = 14
for c in range(2, 7): ws6.column_dimensions[get_column_letter(c)].width = 18

r = 1
ws6.cell(r, 1, "Casa Yano — Forward Bookings on the Books").font = TITLE_FONT
ws6.merge_cells("A1:F1")
r = 2
ws6.cell(r, 1, f"As of {D['generatedAt'][:10]}. Confirmed reservations with deposits received.").font = NOTE_FONT
ws6.merge_cells("A2:F2")
r = 4

headers = ["Month", "PF Target", "Booked Revenue", "% of Target", "Remaining", "Status"]
for i, h in enumerate(headers):
    ws6.cell(r, i+1, h)
hdr_row(ws6, r, 6)
r += 1

fwd_start = r
for f in fwd:
    ws6.cell(r, 1, f["month"]).font = BOLD
    ws6.cell(r, 2, f["pfGross"]).number_format = MONEY
    ws6.cell(r, 2).font = BODY
    ws6.cell(r, 3, f["bookedGross"]).number_format = MONEY
    ws6.cell(r, 3).font = BOLD
    ws6.cell(r, 4, f["pacePct"] / 100).number_format = PCT
    ws6.cell(r, 4).font = BOLD
    ws6.cell(r, 5, max(0, f["pfGross"] - f["bookedGross"])).number_format = MONEY
    ws6.cell(r, 5).font = BODY
    status = "Fully Booked" if f["pacePct"] >= 95 else "Strong" if f["pacePct"] >= 60 else "Building" if f["pacePct"] >= 25 else "Early"
    ws6.cell(r, 6, status).font = BODY
    if f["pacePct"] >= 60:
        for c in range(1, 7): ws6.cell(r, c).fill = GREEN_FILL
    elif f["pacePct"] >= 25:
        for c in range(1, 7): ws6.cell(r, c).fill = YELLOW_FILL
    r += 1

# Totals
for c in range(1, 7): ws6.cell(r, c).border = Border(top=Side(style="medium", color="2D2D2D"))
ws6.cell(r, 1, "TOTAL").font = BOLD
ws6.cell(r, 2, f"=SUM(B{fwd_start}:B{r-1})").number_format = MONEY
ws6.cell(r, 2).font = BOLD
ws6.cell(r, 3, f"=SUM(C{fwd_start}:C{r-1})").number_format = MONEY
ws6.cell(r, 3).font = BOLD
ws6.cell(r, 4, f"=C{r}/B{r}").number_format = PCT
ws6.cell(r, 4).font = BOLD
ws6.cell(r, 5, f"=B{r}-C{r}").number_format = MONEY
ws6.cell(r, 5).font = BOLD

ws6.freeze_panes = "A5"


# ════════════════════════════════════════════════════════
# TAB 7: Pro Forma
# ════════════════════════════════════════════════════════
ws7 = wb.create_sheet("Pro Forma")
ws7.sheet_properties.tabColor = "7B1FA2"
ws7.column_dimensions["A"].width = 30
ws7.column_dimensions["B"].width = 18
ws7.column_dimensions["C"].width = 14

r = 1
ws7.cell(r, 1, "Casa Yano — 2026 Pro Forma (Blended Forecast)").font = TITLE_FONT
ws7.merge_cells("A1:C1")
r = 2
ws7.cell(r, 1, f"Blends {PF['closedMonths']} months of closed actuals with seasonal projections calibrated from actual performance").font = NOTE_FONT
ws7.merge_cells("A2:C2")
r = 4

hdr_row(ws7, r, 3)
ws7.cell(r, 1, "").font = HEADER_FONT
ws7.cell(r, 2, "Amount").font = HEADER_FONT
ws7.cell(r, 3, "% of Gross").font = HEADER_FONT
r += 1

pf_gross = PF["gross"]
wf = PF["waterfall"]

pl_lines = [
    ("Gross Revenue", pf_gross, True, False, None),
    ("OTA Commissions", abs(wf[1]["value"]), False, True, None),
    ("Taxes (TOT)", abs(wf[2]["value"]), False, True, None),
    ("Processing Fees", abs(wf[3]["value"]), False, True, None),
    ("Net to Owner", PF["netOwner"], True, False, LIGHT_GOLD),
    ("Direct OpEx (Cleaning, Supplies, etc.)", PF["opex"], False, True, None),
    ("Management Fee (10%)", PF["mgmtFee"], False, True, None),
    ("Property Tax", PF["propertyTax"], False, True, None),
    ("Insurance", PF["insurance"], False, True, None),
    ("Other Fixed Costs", PF["otherFixed"], False, True, None),
    ("Net Operating Income", PF["noiAfterKnown"], True, False, GREEN_FILL),
]

for label, val, is_bold, is_neg, fill in pl_lines:
    ws7.cell(r, 1, f"  {label}" if is_neg else label).font = BOLD if is_bold else BODY
    displayed = -val if is_neg else val
    ws7.cell(r, 2, displayed).number_format = MONEY
    ws7.cell(r, 2).font = BOLD if is_bold else BODY
    if label in ("Net to Owner", "Net Operating Income", "Gross Revenue"):
        pct_val = val / pf_gross if pf_gross else 0
        ws7.cell(r, 3, pct_val).number_format = PCT
        ws7.cell(r, 3).font = BOLD
    if fill:
        for c in range(1, 4): ws7.cell(r, c).fill = fill
    ws7.cell(r, 1).border = THIN_B
    ws7.cell(r, 2).border = THIN_B
    ws7.cell(r, 3).border = THIN_B
    r += 1

r += 1
ws7.cell(r, 1, "MODEL INPUTS").font = SECTION_FONT
ws7.cell(r, 1).border = THICK_B
ws7.cell(r, 2).border = THICK_B
r += 1
inputs = [
    ("Closed Months Used for Calibration", PF["closedMonths"], None),
    ("Baseline ADR (de-seasonalized)", PF["baselineAdr"], MONEY),
    ("Baseline Occupancy (de-seasonalized)", PF["baselineOcc"] / 100, PCT),
    ("Max Occupancy Cap", 0.92, PCT),
    ("Back-test MAPE (Gross Revenue)", fa["mapeGross"] / 100 if fa["mapeGross"] else "N/A", PCT if fa["mapeGross"] else None),
]
for label, val, fmt in inputs:
    r = write_item(ws7, r, label, val, fmt)

r += 1
ws7.cell(r, 1, "Methodology: Actual monthly ADR and occupancy are divided by their seasonal index to").font = NOTE_FONT
ws7.merge_cells(f"A{r}:C{r}")
r += 1
ws7.cell(r, 1, "strip out seasonality, revealing baseline performance. Forward months multiply this baseline").font = NOTE_FONT
ws7.merge_cells(f"A{r}:C{r}")
r += 1
ws7.cell(r, 1, "by the appropriate seasonal index. The model improves with every data upload.").font = NOTE_FONT
ws7.merge_cells(f"A{r}:C{r}")

ws7.freeze_panes = "A5"


# ── Save ──
OUTPUT = Path(__file__).parent / "Casa_Yano_Lender_Package.xlsx"
wb.save(OUTPUT)
print(f"Saved: {OUTPUT}")
print(f"Tabs: {', '.join(wb.sheetnames)}")
