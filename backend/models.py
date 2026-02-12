from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Item(Base):
    """Product/item master data - info about a product by barcode."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    category = Column(String, nullable=True)  # mid-level OFF category tag for similarity matching
    image_url = Column(String, nullable=True)
    unit = Column(String, default="pcs")  # pcs, g, kg, ml, L
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    inventory = relationship("Inventory", back_populates="item", uselist=False)


class Inventory(Base):
    """Current inventory - how much of an item we have."""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), unique=True, nullable=False)
    quantity = Column(Float, default=0)
    location = Column(String, nullable=True)  # pantry, fridge, freezer
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    item = relationship("Item", back_populates="inventory")


class ScanHistory(Base):
    """Log of all scans for analytics."""
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, nullable=False)
    action = Column(String, nullable=False)  # add, remove, check
    quantity = Column(Float, default=1)
    timestamp = Column(DateTime, server_default=func.now())
