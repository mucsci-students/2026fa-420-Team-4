import json

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.json_validator import validate_config_dict
from backend.models.session_store import store
from scheduler.config import CombinedConfig

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.post("/upload")
async def upload_config(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))

        is_valid, errors = validate_config_dict(data)
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})

        combined_config = CombinedConfig.model_validate(data)

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
