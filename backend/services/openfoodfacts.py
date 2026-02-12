import httpx
from typing import Optional


def pick_category(categories_tags: list[str]) -> Optional[str]:
    """Pick the mid-level OFF category tag for similarity matching.

    OFF returns categories from broadest to most specific. The middle en: tag
    hits the sweet spot — specific enough to be meaningful (e.g. "cereal-pastas",
    "plant-based-spreads") but broad enough to group similar products together.
    """
    en_tags = [t for t in categories_tags if t.startswith("en:")]
    if not en_tags:
        return categories_tags[len(categories_tags) // 2] if categories_tags else None
    return en_tags[len(en_tags) // 2]


async def lookup_barcode(barcode: str) -> Optional[dict]:
    """
    Look up a barcode in the Open Food Facts database.
    Returns product info if found, None otherwise.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == 1:  # Product found
                product = data.get("product", {})
                categories_tags = product.get("categories_tags", [])
                return {
                    "name": product.get("product_name") or product.get("product_name_en") or "Unknown",
                    "brand": product.get("brands"),
                    "category": pick_category(categories_tags),
                    "image_url": product.get("image_front_small_url") or product.get("image_url"),
                    "quantity_info": product.get("quantity"),  # e.g., "500g"
                }
            return None
    except Exception as e:
        print(f"Error looking up barcode {barcode}: {e}")
        return None
