# Asset Lifecycle Dashboard (React + FastAPI)

Tracks a fleet of ~10,000 leased devices (4-year lease), HP vendor stock (5,684) and HP replenishment orders (453).

## Run it
```bash
# 1) data (re-generates data/asset_data.xlsx relative to today's date)
pip install -r backend/requirements.txt
python scripts/generate_data.py

# 2) backend  -> http://localhost:8000/docs
cd backend && uvicorn app.main:app --reload --port 8000

# 3) frontend -> http://localhost:5173  (new terminal)
cd frontend && npm install && npm run dev
```

## Pages
| Page | What it shows |
|---|---|
| Lease Lifecycle | expired / expiring in 30, 60, 90 days, monthly timeline, by layout & type, searchable device table |
| Replenishment (HP) | 453 devices on order by status, type, layout, ETA |
| HP Stock Aging | stock older than 30 days / 3 months / 1 year / 2 years |
| Stock Availability Grid | layouts (x) vs device types (y): in / low / out of stock (low threshold adjustable) |
