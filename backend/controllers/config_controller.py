# backend/controllers/config_controller.py
from fastapi import APIRouter, HTTPException, UploadFile, File
import json
from backend.models.session_store import store
from backend.json_validator import validate_config_dict
from scheduler.config import CombinedConfig

router = APIRouter(prefix="/api/config", tags=["Configuration"])

@router.post("/upload")
async def upload_config(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        
        # 1. Validate structure using Sprint 1 validator logic
        is_valid, errors = validate_config_dict(data)
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})

        # 2. Parse into CombinedConfig object
        combined_config = CombinedConfig.model_validate(data)

        # 3. Save to global session store
        store.raw_config = data
        store.config_object = combined_config
        store.is_loaded = True

        return {
            "message": "Configuration uploaded and validated successfully",
            "config": store.raw_config,
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")

@router.get("/")
def get_config():
    if not store.is_loaded:
        return {"status": "empty", "config": {}}
    return {"status": "loaded", "config": store.raw_config}