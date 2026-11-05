"""Pure pandas analytics (no FastAPI imports) so every function is easy to unit-test."""
import os
from datetime import date
from pathlib import Path

import pandas as pd

DATA_FILE = Path(os.getenv("ASSET_DATA_FILE", Path(__file__).resolve().parents[2] / "data" / "asset_data.xlsx"))

LAYOUTS = ["DE", "FR", "UK", "IT", "DK", "HU", "SE"]
DEVICE_TYPES = [
    "Standard Laptop S", "Standard Laptop M", "Standard Laptop L", "Executive Laptop",
    'Mobile Workstation 16"', 'Mobile Workstation 18"', "Tablet",
]
LEASE_STATUSES = ["expired", "expiring_30", "expiring_60", "expiring_90", "active"]

# cumulative "older than" thresholds requested for the HP stock aging page
AGING_THRESHOLDS = [("> 30 days", 30), ("> 3 months", 90), ("> 1 year", 365), ("> 2 years", 730)]
# mutually exclusive bands, used for the chart
AGING_BANDS = [("0-30 days", 0, 30), ("31-90 days", 31, 90), ("91-365 days", 91, 365),
               ("1-2 years", 366, 730), ("> 2 years", 731, 10**6)]


class DataStore:
    """Loads the workbook once and keeps it in memory (10k rows is tiny)."""

    def __init__(self, path: Path = DATA_FILE):
        sheets = pd.read_excel(path, sheet_name=None)
        self.deployed = sheets["Deployed Devices"]
        self.stock = sheets["HP Vendor Stock"]
        self.orders = sheets["Replenishment Orders"]
        for df, cols in ((self.deployed, ["lease_start", "lease_end"]), (self.stock, ["received_date"]),
                         (self.orders, ["order_date", "expected_delivery"])):
            for c in cols:
                df[c] = pd.to_datetime(df[c])

    def with_lease_status(self, today: date | None = None) -> pd.DataFrame:
        today_ts = pd.Timestamp(today or date.today())
        df = self.deployed.copy()
        df["days_to_expiry"] = (df["lease_end"] - today_ts).dt.days
        d = df["days_to_expiry"]
        df["lease_status"] = "active"
        df.loc[d <= 90, "lease_status"] = "expiring_90"
        df.loc[d <= 60, "lease_status"] = "expiring_60"
        df.loc[d <= 30, "lease_status"] = "expiring_30"
        df.loc[d < 0, "lease_status"] = "expired"
        return df


def _counts(df: pd.DataFrame, col: str, order: list | None = None) -> list[dict]:
    s = df[col].value_counts()
    if order:
        s = s.reindex(order, fill_value=0)
    return [{col: k, "count": int(v)} for k, v in s.items()]


def summary(store: DataStore, today: date | None = None) -> dict:
    df = store.with_lease_status(today)
    d = df["days_to_expiry"]
    total = len(df)
    return {
        "total_devices": total,
        "expired": int((d < 0).sum()),
        "expiring_30": int(((d >= 0) & (d <= 30)).sum()),
        "expiring_60": int(((d >= 0) & (d <= 60)).sum()),
        "expiring_90": int(((d >= 0) & (d <= 90)).sum()),
        "expiring_180": int(((d >= 0) & (d <= 180)).sum()),
        "hp_share_pct": round(100 * (df["vendor"] == "HP").mean(), 1),
        "vendor_mix": _counts(df, "vendor"),
        "hp_stock_total": len(store.stock),
        "replenishment_total": len(store.orders),
    }


def expiry_timeline(store: DataStore, months: int = 12, today: date | None = None) -> list[dict]:
    """Number of leases ending in each of the next `months` calendar months (current month included)."""
    df = store.with_lease_status(today)
    t = pd.Timestamp(today or date.today())
    start = t.to_period("M")
    periods = [start + i for i in range(months)]
    per = df["lease_end"].dt.to_period("M")
    upcoming = df[(df["days_to_expiry"] >= 0)]
    counts = upcoming["lease_end"].dt.to_period("M").value_counts()
    return [{"month": str(p), "count": int(counts.get(p, 0))} for p in periods]


def expiry_breakdown(store: DataStore, days: int = 90, today: date | None = None) -> dict:
    df = store.with_lease_status(today)
    win = df[(df["days_to_expiry"] >= 0) & (df["days_to_expiry"] <= days)]
    return {"days": days, "total": len(win),
            "by_layout": _counts(win, "layout", LAYOUTS),
            "by_device_type": _counts(win, "device_type", DEVICE_TYPES),
            "by_vendor": _counts(win, "vendor")}


def list_devices(store: DataStore, status: str | None = None, layout: str | None = None,
                 device_type: str | None = None, vendor: str | None = None, search: str | None = None,
                 page: int = 1, page_size: int = 25, today: date | None = None) -> dict:
    df = store.with_lease_status(today)
    if status == "expiring_30":
        df = df[(df["days_to_expiry"] >= 0) & (df["days_to_expiry"] <= 30)]
    elif status == "expiring_60":
        df = df[(df["days_to_expiry"] >= 0) & (df["days_to_expiry"] <= 60)]
    elif status == "expiring_90":
        df = df[(df["days_to_expiry"] >= 0) & (df["days_to_expiry"] <= 90)]
    elif status == "expired":
        df = df[df["days_to_expiry"] < 0]
    elif status == "active":
        df = df[df["days_to_expiry"] > 90]
    if layout:
        df = df[df["layout"] == layout]
    if device_type:
        df = df[df["device_type"] == device_type]
    if vendor:
        df = df[df["vendor"] == vendor]
    if search:
        q = search.strip().lower()
        df = df[df["serial_number"].str.lower().str.contains(q, regex=False)
                | df["asset_tag"].str.lower().str.contains(q, regex=False)]
    df = df.sort_values("lease_end")
    total = len(df)
    chunk = df.iloc[(page - 1) * page_size: page * page_size].copy()
    for c in ("lease_start", "lease_end"):
        chunk[c] = chunk[c].dt.strftime("%Y-%m-%d")
    return {"total": total, "page": page, "page_size": page_size,
            "items": chunk[["serial_number", "asset_tag", "vendor", "model", "device_type", "layout",
                            "lease_start", "lease_end", "days_to_expiry", "lease_status"]].to_dict("records")}


def replenishment(store: DataStore, today: date | None = None) -> dict:
    o = store.orders.copy()
    t = pd.Timestamp(today or date.today())
    o["days_to_delivery"] = (o["expected_delivery"] - t).dt.days
    items = o.sort_values("expected_delivery").copy()
    for c in ("order_date", "expected_delivery"):
        items[c] = items[c].dt.strftime("%Y-%m-%d")
    return {"total": len(o), "vendor": "HP",
            "by_status": _counts(o, "status"),
            "by_device_type": _counts(o, "device_type", DEVICE_TYPES),
            "by_layout": _counts(o, "layout", LAYOUTS),
            "items": items.head(200).to_dict("records")}


def stock_aging(store: DataStore, today: date | None = None) -> dict:
    s = store.stock.copy()
    t = pd.Timestamp(today or date.today())
    s["age_days"] = (t - s["received_date"]).dt.days
    total = len(s)
    thresholds = [{"label": label, "days": days, "count": int((s["age_days"] > days).sum()),
                   "pct": round(100 * (s["age_days"] > days).mean(), 1)} for label, days in AGING_THRESHOLDS]
    bands, by_type = [], {t_: {"device_type": t_} for t_ in DEVICE_TYPES}
    for label, lo, hi in AGING_BANDS:
        m = (s["age_days"] >= lo) & (s["age_days"] <= hi)
        bands.append({"band": label, "count": int(m.sum())})
        for t_, n in s[m]["device_type"].value_counts().reindex(DEVICE_TYPES, fill_value=0).items():
            by_type[t_][label] = int(n)
    oldest = s.sort_values("age_days", ascending=False).head(15).copy()
    oldest["received_date"] = oldest["received_date"].dt.strftime("%Y-%m-%d")
    return {"total": total, "thresholds": thresholds, "bands": bands,
            "by_device_type": list(by_type.values()),
            "oldest": oldest[["serial_number", "model", "device_type", "layout", "received_date", "age_days"]]
            .to_dict("records")}


def stock_grid(store: DataStore, low_threshold: int = 25) -> dict:
    """Layout (x) vs device type (y) with in / low / out of stock status.

    status: out_of_stock if 0 devices, low_stock if 1..low_threshold, else in_stock.
    `on_order` shows replenishment units already ordered for the same cell.
    """
    stock = store.stock.groupby(["layout", "device_type"]).size()
    ordered = store.orders.groupby(["layout", "device_type"]).size()
    cells, summary_ = [], {"in_stock": 0, "low_stock": 0, "out_of_stock": 0}
    for dt in DEVICE_TYPES:
        for lay in LAYOUTS:
            n = int(stock.get((lay, dt), 0))
            status = "out_of_stock" if n == 0 else "low_stock" if n <= low_threshold else "in_stock"
            summary_[status] += 1
            cells.append({"layout": lay, "device_type": dt, "count": n, "status": status,
                          "on_order": int(ordered.get((lay, dt), 0))})
    return {"layouts": LAYOUTS, "device_types": DEVICE_TYPES, "low_threshold": low_threshold,
            "summary": summary_, "cells": cells}
