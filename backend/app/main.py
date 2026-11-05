from datetime import date

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import analytics as a

app = FastAPI(title="Asset Lifecycle API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

store = a.DataStore()


@app.get("/api/health")
def health():
    return {"status": "ok", "today": date.today().isoformat()}


@app.get("/api/summary")
def summary():
    return a.summary(store)


@app.get("/api/lifecycle/timeline")
def timeline(months: int = Query(12, ge=1, le=36)):
    return a.expiry_timeline(store, months)


@app.get("/api/lifecycle/breakdown")
def breakdown(days: int = Query(90, ge=1, le=730)):
    return a.expiry_breakdown(store, days)


@app.get("/api/devices")
def devices(status: str | None = None, layout: str | None = None, device_type: str | None = None,
            vendor: str | None = None, search: str | None = None,
            page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    return a.list_devices(store, status, layout, device_type, vendor, search, page, page_size)


@app.get("/api/replenishment")
def replenishment():
    return a.replenishment(store)


@app.get("/api/stock/aging")
def aging():
    return a.stock_aging(store)


@app.get("/api/stock/grid")
def grid(low_threshold: int = Query(25, ge=1, le=500)):
    return a.stock_grid(store, low_threshold)
