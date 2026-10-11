# backend/back_controllers/generator_controller.py
from fastapi import APIRouter, HTTPException
from backend.models.session_store import store
from scheduler import Scheduler

router = APIRouter(prefix="/api/generator", tags=["Generator"])

@router.post("/run")
def run_generator():
    if not store.is_loaded or store.config_object is None:
        raise HTTPException(
            status_code=400,
            detail="No configuration loaded. Upload a valid configuration first."
        )

    try:
        # Instantiate scheduler with loaded CombinedConfig object
        scheduler = Scheduler(store.config_object)
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