"""
Main Application Entry Point - FastAPI Server and Static File Mounting
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading

from app.api.routes import router as api_router
from app.services.market_data import warmup_cache

app = FastAPI(
    title="StockAI - AI-Powered Stock Analysis Platform",
    description="Professional Indian Stock Market (NSE/BSE) and Global Multi-Factor Analysis Engine",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    """Trigger background warmup for instant sub-second responses"""
    threading.Thread(target=warmup_cache, daemon=True).start()

# Enable CORS for external API integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Locate static directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    """Serves the main single page dashboard interface"""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "StockAI Platform", "version": "1.0.0"}


if __name__ == "__main__":
    print("=" * 60)
    print("  StockAI Platform is starting on http://localhost:8000")
    print("  Open http://localhost:8000 in your browser to view")
    print("=" * 60)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
