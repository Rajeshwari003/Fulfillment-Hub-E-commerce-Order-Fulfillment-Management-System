## What it solves

- One dashboard for order visibility
- Priority and delayed-order visibility
- Inventory visibility across main + secondary warehouses
- Stock transfer from secondary to main warehouse
- Simple picking → packing → staging → shipping workflow
- Staging locations and box IDs to reduce misplaced packages
- Courier pickup visibility
- Trackable operational issues

## Tech stack

- Frontend: React + Vite + Axios + Lucide React
- Backend: Python + Flask + Flask-SQLAlchemy + Flask-CORS
- Database: SQLite

## Project structure

```text
fulfillment-hub/
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       └── styles.css
└── README.md
```

## Requirements

- Python 3.10+
- Node.js 18+
- npm 9+

## Run the backend

Open Terminal / PowerShell:

```bash
cd backend
python -m venv .venv
```

### Windows

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API runs at:

```text
http://localhost:5000
```

The SQLite database is created automatically on first run and seeded with dummy data.

## Run the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite displays, normally:

```text
http://localhost:5173
```

## Demo flow for the interview

Use the seeded `ORD-1024` example:

1. Open Dashboard and show the urgent order + inventory warning.
2. Open Orders and click `ORD-1024`.
3. Show that `SHOE101` has 0 units in Main and 8 in Secondary.
4. Go to Inventory and transfer 2 units of `SHOE101` to Main.
5. Return to the order and start Picking.
6. Confirm the item is picked/packed.
7. Move it to Staging; the app creates a box ID and staging location.
8. Open Shipping and show the courier pickup readiness.
9. Open Issues and resolve an operational issue.

## Important design decisions

1. **Exception-first dashboard:** The dashboard surfaces priority orders, delays, stock problems and open issues because these are the things most likely to cause missed deadlines.
2. **Simple warehouse UI:** The picking/packing screens use large, explicit actions because the scenario says warehouse staff are experienced but not very comfortable with technology.
3. **Inventory by warehouse:** Main and secondary stock are shown separately so a stock mismatch is visible before picking starts.
4. **Trackable staging:** Box IDs and staging locations reduce the chance that packed orders are misplaced.
5. **No real courier integration:** This is intentionally a self-contained demo using dummy pickup data, since the assignment provides no external courier systems.
