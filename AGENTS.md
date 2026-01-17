# almntshn - Design Document

## Overview

**almntshn** (alimentation) is a home food inventory tracking app. It allows a household to:
- Scan barcodes when shopping or unpacking groceries
- Check if an item is already in stock before buying
- Track quantities of items at home
- Maintain a searchable inventory

## Target Users

- A household with iPhones
- Accessed via mobile web browser (not a native app)
- Eventually hosted on a Raspberry Pi via Tailscale for private, always-on access

## Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Python + FastAPI | Modern, async, easy to develop |
| Database | SQLite | No server needed, perfect for Pi, easy backups |
| Frontend | Vanilla HTML/CSS/JS | Lightweight, no build step, mobile-first |
| Barcode scanning | html5-qrcode library | Works in browser, iOS Safari compatible |
| Product lookup | Open Food Facts API | Free, no API key, good coverage |
| Hosting (future) | Raspberry Pi + Tailscale | Private network, HTTPS via MagicDNS |

## Data Model

```
Item (master product data)
├── id, barcode (unique), name, brand, category, image_url, unit
└── One item can have one inventory record

Inventory (current stock)
├── id, item_id (FK), quantity, location, updated_at
└── Tracks how much of each item we have

ScanHistory (audit log)
├── id, barcode, action (add/remove/check), quantity, timestamp
└── For future analytics (what do we buy most, etc.)
```

## Key Design Decisions

1. **Barcode as primary identifier**: Items are uniquely identified by barcode. This matches how users interact (scan something → see info).

2. **Separate Item vs Inventory**: Item holds static product info (name, brand). Inventory holds dynamic state (quantity). This allows knowing about products even when quantity is 0.

3. **Open Food Facts for product lookup**: When a new barcode is scanned, we query OFF to auto-fill product name/brand/image. Falls back to manual entry if not found.

4. **Quick-add workflow**: The most common action is "I bought this, add 1". The UI optimizes for this with a single tap.

5. **Mobile-first, high-contrast UI**: Plain black/white design, large touch targets (44px minimum), works well in bright supermarket lighting.

6. **No authentication (for now)**: Single household use case. All users on the Tailnet are trusted.

## Development Setup

```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Uses `uv` exclusively for Python dependency management
- No Docker needed for development
- SQLite database created automatically in `data/inventory.db`

## API Design

All endpoints under `/api/`:

### Scanning & Inventory Management
- `POST /api/inventory/scan` - Check if barcode exists, return quantity + product info
- `POST /api/inventory/quick-add` - Add 1 to inventory (creates item if new)
- `POST /api/inventory/adjust` - Adjust quantity by delta (+/-)
- `GET /api/inventory/` - List inventory with optional search

### Item Management
- `GET /api/items/` - List all known items
- `POST /api/items/` - Create item manually
- `GET /api/items/barcode/{barcode}` - Lookup by barcode
- `PUT /api/items/{id}` - Update item details
- `DELETE /api/items/{id}` - Delete item and its inventory

## Phased Roadmap

### Phase 1: MVP ✅ (Current)
- [x] Barcode scanning via phone camera
- [x] Add/remove items from inventory
- [x] Manual quantity adjustment (+/-)
- [x] Basic search by name
- [x] Auto-lookup via Open Food Facts
- [x] Mobile-friendly high-contrast UI

### Phase 2: Usability
- [ ] Shopping list with "do we have this?" indicator
- [ ] Categories/locations (fridge, pantry, freezer)
- [ ] Expiry date tracking
- [ ] Low stock alerts
- [ ] Quick scan mode (continuous scanning)

### Phase 3: Polish
- [ ] PWA support (installable on iPhone home screen)
- [ ] Offline mode with sync
- [ ] Multi-user support (who added what)
- [ ] Scan history view
- [ ] Data export/backup

### Phase 4: Deployment
- [ ] Docker container for Pi deployment
- [ ] Tailscale setup documentation
- [ ] Automatic database backups
- [ ] systemd service for auto-start

## File Structure

```
almntshn/
├── AGENTS.md                # This file - design & context
├── README.md                # Quick start guide
├── backend/
│   ├── pyproject.toml       # Python dependencies (uv)
│   ├── main.py              # FastAPI app, serves frontend
│   ├── database.py          # SQLite connection
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routers/
│   │   ├── items.py         # Item CRUD endpoints
│   │   └── inventory.py     # Inventory & scanning endpoints
│   └── services/
│       └── openfoodfacts.py # External API integration
├── frontend/
│   ├── index.html           # Single-page app shell
│   ├── css/
│   │   └── style.css        # Mobile-first styles
│   └── js/
│       ├── api.js           # Backend API client
│       ├── scanner.js       # html5-qrcode wrapper
│       └── app.js           # UI logic & state
└── data/
    └── inventory.db         # SQLite database (gitignored)
```

## Known Limitations / Future Considerations

1. **HTTPS required for camera**: Browsers require secure context for camera access. Tailscale solves this with MagicDNS. For local dev, use manual barcode entry or localhost.

2. **No offline support yet**: Requires network connection. PWA with local storage sync planned for Phase 3.

3. **Single-household assumption**: No user accounts or permissions. Everyone can see and modify everything.

4. **Open Food Facts coverage**: Not all products exist in OFF, especially store brands or regional products. Manual entry fallback exists.
