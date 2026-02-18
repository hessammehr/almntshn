# almntshn

Home food inventory tracker with barcode scanning.

## Features

- 📷 Scan barcodes with your phone camera
- 🔍 Automatic product lookup via Open Food Facts
- ➕ Quick add/remove from inventory
- 📋 Search and browse your inventory
- 📱 Mobile-first, high-contrast UI

## Running locally

From the repo root:

```bash
make serve
```

Then open http://localhost:8000 in your browser.

For phone/camera testing, use Tailscale HTTPS:

```bash
make serve-ts
```

The command prints the https://<your-hostname>.ts.net URL to open on your phone.

> **Note:** Camera access on phones requires HTTPS; plain HTTP on a local IP won’t work.

## Project structure

```
almntshn/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLite database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── items.py         # Item CRUD endpoints
│   │   └── inventory.py     # Inventory management
│   └── services/
│       └── openfoodfacts.py # Product lookup API
├── frontend/
│   ├── index.html           # Main HTML page
│   ├── css/style.css        # Styles
│   └── js/
│       ├── api.js           # Backend API client
│       ├── scanner.js       # Barcode scanner
│       └── app.js           # Main app logic
└── data/
    └── inventory.db         # SQLite database (created on first run)
```

## API Endpoints

- `POST /api/inventory/scan` - Check if a barcode is in inventory
- `POST /api/inventory/quick-add` - Add 1 of an item (creates if new)
- `POST /api/inventory/adjust` - Adjust quantity (+/-)
- `GET /api/inventory/` - List all inventory
- `GET /api/items/` - List all known items
- `POST /api/items/` - Create a new item
