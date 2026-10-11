# backend/back_controllers/generator_controller.py
from fastapi import APIRouter, HTTPException, Query
from backend.models.session_store import store
from scheduler import Scheduler

router = APIRouter(prefix="/api/generator", tags=["Generator"])

@router.post("/run")
def run_generator(limit: int | None = Query(default=None, ge=0)):
    if not store.is_loaded or store.config_object is None:
        raise HTTPException(
            status_code=400,
            detail="No configuration loaded. Upload a valid configuration first."
        )

    if limit == 0:
        store.schedule = []
        return {
            "status": "success",
            "count": 0,
            "schedules": [],
        }

    try:
        # Instantiate scheduler with loaded CombinedConfig object
        config = (
            store.config_object.model_copy(update={"limit": limit})
            if limit is not None
            else store.config_object
        )
        scheduler = Scheduler(config)
        schedules = []

        # Iterate over generated schedules
        for schedule_idx, model in enumerate(scheduler.get_models(), start=1):
            schedules.append({
                "schedule_id": schedule_idx,
                "courses": [course.as_csv() for course in model]
            })

        store.schedule = schedules
        return {
            "status": "success",
            "count": len(schedules),
            "schedules": schedules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduling error: {str(e)}")