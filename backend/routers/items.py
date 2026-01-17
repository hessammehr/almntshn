from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Item, Inventory
from schemas import ItemCreate, ItemUpdate, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=List[ItemResponse])
def list_items(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    """List all known items, optionally filtered by search term."""
    query = db.query(Item)
    if search:
        query = query.filter(Item.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


@router.get("/barcode/{barcode}", response_model=ItemResponse)
def get_item_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """Get an item by its barcode."""
    item = db.query(Item).filter(Item.barcode == barcode).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get an item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item."""
    existing = db.query(Item).filter(Item.barcode == item.barcode).first()
    if existing:
        raise HTTPException(status_code=400, detail="Item with this barcode already exists")
    
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    """Update an item."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Delete an item and its inventory record."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Delete associated inventory first
    db.query(Inventory).filter(Inventory.item_id == item_id).delete()
    db.delete(db_item)
    db.commit()
    return {"ok": True}
