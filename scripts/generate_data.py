"""Generate a synthetic asset dataset -> data/asset_data.xlsx

Sheets
  Deployed Devices      ~10,000 devices on a 4-year lease (80% HP, 20% Lenovo/Surface/Dell)
  HP Vendor Stock       5,684 HP devices sitting at the vendor, shipped directly against ServiceNow requests
  Replenishment Orders  453 HP devices ordered to replenish that stock

Run:  python scripts/generate_data.py
"""
import random
import string
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

SEED = 42
N_DEPLOYED = 10_000
N_HP_STOCK = 5_684
N_ORDERED = 453
LEASE_YEARS = 4

LAYOUTS = ["DE", "FR", "UK", "IT", "DK", "HU", "SE"]
LAYOUT_WEIGHTS = [24, 18, 22, 12, 7, 8, 9]

DEVICE_TYPES = [
    "Standard Laptop S", "Standard Laptop M", "Standard Laptop L", "Executive Laptop",
    'Mobile Workstation 16"', 'Mobile Workstation 18"', "Tablet",
]
TYPE_WEIGHTS = [14, 36, 18, 10, 8, 4, 10]

VENDORS = ["HP", "Lenovo", "Microsoft Surface", "Dell"]
VENDOR_WEIGHTS = [80, 7, 6, 7]

MODELS = {
    "HP": {"Standard Laptop S": "HP EliteBook 630 G10", "Standard Laptop M": "HP EliteBook 840 G10",
           "Standard Laptop L": "HP EliteBook 860 G10", "Executive Laptop": "HP Elite Dragonfly G4",
           'Mobile Workstation 16"': "HP ZBook Power G10", 'Mobile Workstation 18"': "HP ZBook Fury 16 G10",
           "Tablet": "HP Elite x2 G8"},
    "Lenovo": {"Standard Laptop S": "ThinkPad L13", "Standard Laptop M": "ThinkPad T14",
               "Standard Laptop L": "ThinkPad T16", "Executive Laptop": "ThinkPad X1 Carbon",
               'Mobile Workstation 16"': "ThinkPad P16s", 'Mobile Workstation 18"': "ThinkPad P1 Gen 6",
               "Tablet": "ThinkPad X12 Detachable"},
    "Microsoft Surface": {"Standard Laptop S": "Surface Laptop Go 3", "Standard Laptop M": "Surface Laptop 5 13.5",
                          "Standard Laptop L": "Surface Laptop 5 15", "Executive Laptop": "Surface Laptop Studio 2",
                          'Mobile Workstation 16"': "Surface Laptop Studio 2", 'Mobile Workstation 18"': "Surface Laptop Studio 2",
                          "Tablet": "Surface Pro 9"},
    "Dell": {"Standard Laptop S": "Latitude 3440", "Standard Laptop M": "Latitude 5440",
             "Standard Laptop L": "Latitude 5540", "Executive Laptop": "Latitude 9440",
             'Mobile Workstation 16"': "Precision 5680", 'Mobile Workstation 18"': "Precision 7680",
             "Tablet": "Latitude 7230 Rugged Tablet"},
}

# Cells (layout, type) forced to be out-of-stock / low-stock so the grid is interesting.
FORCED_ZERO = {("HU", 'Mobile Workstation 18"'), ("DK", "Tablet"), ("SE", 'Mobile Workstation 18"'),
               ("IT", "Executive Laptop"), ("HU", "Tablet")}
FORCED_LOW = {("DK", 'Mobile Workstation 18"'): 6, ("SE", "Executive Laptop"): 14, ("HU", "Executive Laptop"): 9,
              ("DK", 'Mobile Workstation 16"'): 18, ("FR", 'Mobile Workstation 18"'): 22, ("IT", "Tablet"): 11,
              ("SE", "Tablet"): 20, ("DK", "Standard Laptop S"): 17}

rng = random.Random(SEED)
TODAY = date.today()
_used = set()


def serial(vendor: str) -> str:
    alnum = string.ascii_uppercase + string.digits
    while True:
        if vendor == "HP":
            s = "5CG" + "".join(rng.choices(alnum, k=7))
        elif vendor == "Lenovo":
            s = rng.choice(["PF", "PW", "R9"]) + "".join(rng.choices(alnum, k=6))
        elif vendor == "Dell":
            s = "".join(rng.choices(alnum, k=7))
        else:
            s = "".join(rng.choices(string.digits, k=12))
        if s not in _used:
            _used.add(s)
            return s


def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # 29 Feb
        return d.replace(year=d.year + years, day=28)


def deployed() -> pd.DataFrame:
    rows = []
    for i in range(N_DEPLOYED):
        vendor = rng.choices(VENDORS, VENDOR_WEIGHTS)[0]
        dtype = rng.choices(DEVICE_TYPES, TYPE_WEIGHTS)[0]
        # lease starts spread over the last ~4.3 years, so some leases already ended and many end soon
        start = TODAY - timedelta(days=rng.randint(0, int(365.25 * LEASE_YEARS) + 120))
        rows.append({
            "serial_number": serial(vendor),
            "asset_tag": f"AT{100000 + i}",
            "vendor": vendor,
            "model": MODELS[vendor][dtype],
            "device_type": dtype,
            "layout": rng.choices(LAYOUTS, LAYOUT_WEIGHTS)[0],
            "lease_start": start,
            "lease_end": add_years(start, LEASE_YEARS),
            "assigned_to": f"user{rng.randint(1000, 99999)}@example.com",
        })
    return pd.DataFrame(rows)


def stock_cell_counts() -> dict:
    cells = [(l, t) for l in LAYOUTS for t in DEVICE_TYPES]
    weights = {c: LAYOUT_WEIGHTS[LAYOUTS.index(c[0])] * TYPE_WEIGHTS[DEVICE_TYPES.index(c[1])] for c in cells}
    forced = {c: 0 for c in FORCED_ZERO} | FORCED_LOW
    free = [c for c in cells if c not in forced]
    remaining = N_HP_STOCK - sum(forced.values())
    total_w = sum(weights[c] for c in free)
    counts = {c: max(30, int(remaining * weights[c] / total_w)) for c in free}  # free cells stay "in stock"
    diff = remaining - sum(counts.values())
    biggest = max(free, key=lambda c: weights[c])
    counts[biggest] += diff  # absorb rounding so the total is exactly N_HP_STOCK
    counts.update(forced)
    return counts


def hp_stock() -> pd.DataFrame:
    rows = []
    for (layout, dtype), n in stock_cell_counts().items():
        for _ in range(n):
            # most stock is fresh; a long tail is old (>1y, >2y)
            age = int(rng.choice([rng.randint(0, 30), rng.randint(0, 90), rng.randint(0, 365),
                                  rng.randint(30, 400), rng.randint(90, 800), rng.randint(0, 120)]))
            rows.append({
                "serial_number": serial("HP"),
                "vendor": "HP",
                "model": MODELS["HP"][dtype],
                "device_type": dtype,
                "layout": layout,
                "received_date": TODAY - timedelta(days=age),
                "status": "In Stock",
            })
    rng.shuffle(rows)
    return pd.DataFrame(rows)


def orders() -> pd.DataFrame:
    rows = []
    # replenishment leans towards the cells that are low / out of stock
    needy = list(FORCED_ZERO) + list(FORCED_LOW)
    for i in range(N_ORDERED):
        if rng.random() < 0.45:
            layout, dtype = rng.choice(needy)
        else:
            layout = rng.choices(LAYOUTS, LAYOUT_WEIGHTS)[0]
            dtype = rng.choices(DEVICE_TYPES, TYPE_WEIGHTS)[0]
        order_date = TODAY - timedelta(days=rng.randint(0, 40))
        eta = order_date + timedelta(days=rng.randint(14, 45))
        status = "Delayed" if eta < TODAY else rng.choices(["Ordered", "In Transit"], [60, 40])[0]
        rows.append({
            "po_number": f"PO-{TODAY.year}-{4000 + i // 25}",
            "serial_number": serial("HP"),
            "vendor": "HP",
            "model": MODELS["HP"][dtype],
            "device_type": dtype,
            "layout": layout,
            "order_date": order_date,
            "expected_delivery": eta,
            "status": status,
        })
    return pd.DataFrame(rows)


def style(ws, df):
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for col_idx, col in enumerate(df.columns, 1):
        c = ws.cell(row=1, column=col_idx)
        c.font = Font(name="Arial", bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3A5F")
        c.alignment = Alignment(horizontal="center")
        width = max(len(str(col)), int(df[col].astype(str).str.len().max())) + 3
        ws.column_dimensions[get_column_letter(col_idx)].width = min(width, 34)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name="Arial", size=10)
            if hasattr(c.value, "year"):
                c.number_format = "yyyy-mm-dd"


def main():
    out = Path(__file__).resolve().parents[1] / "data" / "asset_data.xlsx"
    out.parent.mkdir(exist_ok=True)
    sheets = {"Deployed Devices": deployed(), "HP Vendor Stock": hp_stock(), "Replenishment Orders": orders()}
    with pd.ExcelWriter(out, engine="openpyxl", datetime_format="yyyy-mm-dd", date_format="yyyy-mm-dd") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
            style(xw.sheets[name], df)
    for name, df in sheets.items():
        print(f"{name:22s} {len(df):>6,} rows")
    print("written ->", out)


if __name__ == "__main__":
    main()
