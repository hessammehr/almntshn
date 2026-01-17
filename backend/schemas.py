from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Item schemas
class ItemBase(BaseModel):
    barcode: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    unit: str = "pcs"


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    unit: Optional[str] = None


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Inventory schemas
class InventoryBase(BaseModel):
    quantity: float = 0
    location: Optional[str] = None


class InventoryUpdate(BaseModel):
    quantity: Optional[float] = None
    location: Optional[str] = None


class InventoryResponse(InventoryBase):
    id: int
    item_id: int
    updated_at: datetime
    item: ItemResponse

    class Config:
        from_attributes = True


# Scan/action schemas
class ScanRequest(BaseModel):
    barcode: str


class AdjustQuantityRequest(BaseModel):
    barcode: str
    delta: float  # positive to add, negative to remove


class QuickAddRequest(BaseModel):
    barcode: str
    name: Optional[str] = None  # If not provided, will look up


# Combined response for scan results
class ScanResult(BaseModel):
    found_in_inventory: bool
    item: Optional[ItemResponse] = None
    quantity: float = 0
    product_info: Optional[dict] = None  # From Open Food Facts if new
