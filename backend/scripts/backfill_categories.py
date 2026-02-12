"""
Migration script: backfill OFF category for existing items.

- Renames 'categories' column back to 'category' if needed
- Fetches the mid-level OFF category tag for every item with a barcode

Usage:
    cd backend && uv run python scripts/backfill_categories.py           # only missing
    cd backend && uv run python scripts/backfill_categories.py --force   # re-fetch all
"""

import argparse
import sqlite3
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import services
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.openfoodfacts import lookup_barcode

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "inventory.db"


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def migrate_schema(conn: sqlite3.Connection):
    """Ensure the items table has 'category' (singular)."""
    columns = get_columns(conn, "items")

    has_category = "category" in columns
    has_categories = "categories" in columns

    if has_category and not has_categories:
        print("Schema already up to date.")
        return

    if has_categories and not has_category:
        # Rename categories → category via table rebuild
        print("Migrating 'categories' → 'category'...")
        conn.execute("ALTER TABLE items RENAME TO items_old")
        conn.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                image_url TEXT,
                unit TEXT DEFAULT 'pcs',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Copy data — clear old categories values since they were comma-separated
        # and need to be re-fetched as single mid-level tags
        conn.execute("""
            INSERT INTO items (id, barcode, name, brand, category, image_url, unit, created_at, updated_at)
            SELECT id, barcode, name, brand, NULL, image_url, unit, created_at, updated_at
            FROM items_old
        """)
        conn.execute("DROP TABLE items_old")
        conn.commit()
        print("Schema migrated. All categories cleared for re-fetch.")
        return

    if not has_category and not has_categories:
        conn.execute("ALTER TABLE items ADD COLUMN category TEXT")
        conn.commit()
        print("Added 'category' column.")
        return

    if has_category and has_categories:
        # Both exist — drop categories, keep category
        print("Both 'category' and 'categories' exist. Rebuilding table...")
        conn.execute("ALTER TABLE items RENAME TO items_old")
        conn.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                image_url TEXT,
                unit TEXT DEFAULT 'pcs',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO items (id, barcode, name, brand, category, image_url, unit, created_at, updated_at)
            SELECT id, barcode, name, brand, category, image_url, unit, created_at, updated_at
            FROM items_old
        """)
        conn.execute("DROP TABLE items_old")
        conn.commit()
        print("Schema cleaned up.")


async def backfill_categories(conn: sqlite3.Connection, force: bool = False):
    """Fetch mid-level OFF category for items.

    By default only fetches for items missing a category.
    With --force, re-fetches for all items.
    """
    if force:
        cursor = conn.execute(
            "SELECT id, barcode, name FROM items WHERE barcode IS NOT NULL AND barcode != 'null'"
        )
    else:
        cursor = conn.execute(
            "SELECT id, barcode, name FROM items "
            "WHERE (category IS NULL OR category = '') "
            "AND barcode IS NOT NULL AND barcode != 'null'"
        )
    items = cursor.fetchall()

    if not items:
        print("Nothing to backfill." if not force else "No items with valid barcodes found.")
        return

    mode = "all" if force else "missing"
    print(f"Fetching category for {len(items)} items ({mode}) from Open Food Facts...\n")

    updated = 0
    skipped = 0

    for item_id, barcode, name in items:
        print(f"  [{item_id}] {name} ({barcode})...", end=" ", flush=True)

        product = await lookup_barcode(barcode)

        if product and product.get("category"):
            conn.execute(
                "UPDATE items SET category = ? WHERE id = ?",
                (product["category"], item_id),
            )
            conn.commit()
            print(f"✓ {product['category']}")
            updated += 1
        else:
            print("✗ not found in OFF")
            skipped += 1

    print(f"\nDone. Updated: {updated}, Not found: {skipped}")


async def main():
    parser = argparse.ArgumentParser(description="Backfill OFF category for inventory items.")
    parser.add_argument(
        "--force", action="store_true",
        help="Re-fetch category for all items, not just those missing one"
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Start the server first to create it.")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    try:
        migrate_schema(conn)
        await backfill_categories(conn, force=args.force)
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
