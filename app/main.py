from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hiverecon.config import get_config
from hiverecon.database import init_db
from app.api.v1.reports import router as reports_router
from app.api.v1.ws import router as ws_router
from app.mcp.server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_config()
    await init_db(cfg.get_database_url())
    yield


app = FastAPI(
    title="HiveRecon",
    description="AI-powered bug bounty reconnaissance framework",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(reports_router)
app.include_router(ws_router, prefix="/api/v1/ws", tags=["websocket"])

# Health check
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
