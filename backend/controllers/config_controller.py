# backend/controllers/config_controller.py
from fastapi import APIRouter
from backend.models.session_store import store

router = APIRouter(prefix="/api/config", tags=["Configuration"])

@router.get("/")
def get_config():
    if not store.is_loaded:
        return {"status": "empty", "config": {}}
    return {"status": "loaded", "config": store.raw_config}