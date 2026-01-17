# almntshn

Home food inventory tracker with barcode scanning.

## Features

- 📷 Scan barcodes with your phone camera
- 🔍 Automatic product lookup via Open Food Facts
- ➕ Quick add/remove from inventory
- 📋 Search and browse your inventory
- 📱 Mobile-first, high-contrast UI

## Running locally

```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open http://localhost:8000 in your browser.

To access from your phone on the same network, use your Mac's local IP (e.g., http://192.168.1.x:8000).

> **Note:** Camera access requires HTTPS on most browsers. For local development on the same device, localhost works. For phone access, you may need to use a tunnel or accept the security warning.

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
