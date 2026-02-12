from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models import Item, Inventory, ScanHistory
from schemas import (
    InventoryResponse, InventoryUpdate, 
    ScanRequest, ScanResult, SimilarItem, AdjustQuantityRequest, QuickAddRequest
)
from services.openfoodfacts import lookup_barcode

router = APIRouter(prefix="/inventory", tags=["inventory"])


def find_similar_items(db: Session, category: str, exclude_item_id: int = None) -> list:
    """Find inventory items with the same OFF category."""
    if not category:
        return []

    query = db.query(Inventory).options(joinedload(Inventory.item)).join(Item).filter(
        Item.category == category,
    )
    if exclude_item_id is not None:
        query = query.filter(Item.id != exclude_item_id)

    return [
        SimilarItem(item=inv.item, quantity=inv.quantity)
        for inv in query.all()
    ]


@router.get("/", response_model=List[InventoryResponse])
def list_inventory(
    skip: int = 0, 
    limit: int = 100, 
    search: str = None,
    in_stock_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all inventory items."""
    query = db.query(Inventory).options(joinedload(Inventory.item))
    
    if search:
        query = query.join(Item).filter(Item.name.ilike(f"%{search}%"))
    
    if in_stock_only:
        query = query.filter(Inventory.quantity > 0)
    
    return query.offset(skip).limit(limit).all()


@router.post("/scan", response_model=ScanResult)
async def scan_barcode(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Scan a barcode to check if we have it.
    Returns item info and current quantity if in inventory.
    If not known, looks up in Open Food Facts.
    Also returns similar items already in inventory (by shared OFF categories).
    """
    # Log the scan
    scan_log = ScanHistory(barcode=request.barcode, action="check")
    db.add(scan_log)
    db.commit()
    
    # Check if we have this item
    item = db.query(Item).filter(Item.barcode == request.barcode).first()
    
    if item:
        inventory = db.query(Inventory).filter(Inventory.item_id == item.id).first()
        similar = find_similar_items(db, item.category, exclude_item_id=item.id)
        return ScanResult(
            found_in_inventory=True,
            item=item,
            quantity=inventory.quantity if inventory else 0,
            similar_items=similar,
        )
    
    # Not in our database - look up in Open Food Facts
    product_info = await lookup_barcode(request.barcode)
    
    # Even for unknown items, check if we have something similar
    similar = []
    if product_info and product_info.get("category"):
        similar = find_similar_items(db, product_info["category"])
    
    return ScanResult(
        found_in_inventory=False,
        product_info=product_info,
        similar_items=similar,
    )


@router.post("/quick-add", response_model=InventoryResponse)
async def quick_add(request: QuickAddRequest, db: Session = Depends(get_db)):
    """
    Quick add: scan a barcode and add 1 to inventory.
    Creates the item if it doesn't exist (looks up in Open Food Facts).
    """
    # Check if item exists
    item = db.query(Item).filter(Item.barcode == request.barcode).first()
    
    if not item:
        # Look up or use provided name
        if request.name:
            item_data = {"name": request.name}
        else:
            item_data = await lookup_barcode(request.barcode)
            if not item_data:
                item_data = {"name": f"Unknown ({request.barcode})"}
        
        item = Item(
            barcode=request.barcode,
            name=item_data.get("name", f"Unknown ({request.barcode})"),
            brand=item_data.get("brand"),
            category=item_data.get("category"),
            image_url=item_data.get("image_url")
        )
        db.add(item)
        db.commit()
        db.refresh(item)
    
    # Get or create inventory record
    inventory = db.query(Inventory).filter(Inventory.item_id == item.id).first()
    if not inventory:
        inventory = Inventory(item_id=item.id, quantity=0)
        db.add(inventory)
    
    # Add 1
    inventory.quantity += 1
    
    # Log the action
    scan_log = ScanHistory(barcode=request.barcode, action="add", quantity=1)
    db.add(scan_log)
    
    db.commit()
    db.refresh(inventory)
    
    return inventory


@router.post("/adjust", response_model=InventoryResponse)
def adjust_quantity(request: AdjustQuantityRequest, db: Session = Depends(get_db)):
    """
    Adjust quantity for an item (positive to add, negative to remove).
    """
    item = db.query(Item).filter(Item.barcode == request.barcode).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found. Scan it first to add.")
    
    inventory = db.query(Inventory).filter(Inventory.item_id == item.id).first()
    if not inventory:
        inventory = Inventory(item_id=item.id, quantity=0)
        db.add(inventory)
    
    inventory.quantity = max(0, inventory.quantity + request.delta)
    
    # Log the action
    action = "add" if request.delta > 0 else "remove"
    scan_log = ScanHistory(barcode=request.barcode, action=action, quantity=abs(request.delta))
    db.add(scan_log)
    
    db.commit()
    db.refresh(inventory)
    
    return inventory


@router.put("/{item_id}", response_model=InventoryResponse)
def update_inventory(item_id: int, update: InventoryUpdate, db: Session = Depends(get_db)):
    """Update inventory details for an item."""
    inventory = db.query(Inventory).filter(Inventory.item_id == item_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory record not found")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(inventory, key, value)
    
    db.commit()
    db.refresh(inventory)
    return inventory


@router.delete("/barcode/{barcode}")
def remove_from_inventory(barcode: str, db: Session = Depends(get_db)):
    """Remove an item from inventory (sets quantity to 0)."""
    item = db.query(Item).filter(Item.barcode == barcode).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    inventory = db.query(Inventory).filter(Inventory.item_id == item.id).first()
    if inventory:
        inventory.quantity = 0
        db.commit()
    
    return {"ok": True}
