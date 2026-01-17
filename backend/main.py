from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from database import engine, Base
from routers import items, inventory

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="almntshn",
    description="Home food inventory tracker",
    version="0.1.0"
)

# Include routers
app.include_router(items.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
