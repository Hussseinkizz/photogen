from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import ROOT, init_db
from app.routes import router
from app.storage import GENERATED_DIR, UPLOAD_DIR, ensure_folders

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_folders()
    init_db()
    yield


app = FastAPI(title="Photogen", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
ensure_folders()
app.include_router(router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")


@app.get("/health")
def health() -> dict[str, object]:
    return {"ok": True, "root": str(ROOT)}
