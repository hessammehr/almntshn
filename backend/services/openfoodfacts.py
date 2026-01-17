import httpx
from typing import Optional


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
                return {
                    "name": product.get("product_name") or product.get("product_name_en") or "Unknown",
                    "brand": product.get("brands"),
                    "category": product.get("categories_tags", [None])[0] if product.get("categories_tags") else None,
                    "image_url": product.get("image_front_small_url") or product.get("image_url"),
                    "quantity_info": product.get("quantity"),  # e.g., "500g"
                }
            return None
    except Exception as e:
        print(f"Error looking up barcode {barcode}: {e}")
        return None
