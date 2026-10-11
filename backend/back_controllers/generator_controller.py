# backend/back_controllers/generator_controller.py
from fastapi import APIRouter, HTTPException, Query
from backend.models.session_store import store
from scheduler import Scheduler

router = APIRouter(prefix="/api/generator", tags=["Generator"])

@router.post("/run")
def run_generator(limit: int | None = Query(default=None, ge=0)):
    """Generate and store schedules for the loaded configuration.

    A supplied limit overrides the configured limit; zero clears stored schedules
    without generation. Return the status, count, and schedules. Raise HTTP 400
    if no configuration is loaded, or HTTP 500 if scheduling fails.
    """
    if not store.is_loaded or store.config_object is None:
        raise HTTPException(
            status_code=400,
            detail="No configuration loaded. Upload a valid configuration first."
        )

    if limit == 0:
        store.schedule = []
        store.generation_running = False
        return {
            "status": "success",
            "count": 0,
            "schedules": [],
        }

    store.generation_running = True
    store.generation_progess = 0

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
            print (f"Processing schedule {schedule_idx}")
            schedules.append({
                "schedule_id": schedule_idx,
                "courses": [course.as_csv() for course in model]
            })
            store.generation_progess = schedule_idx

        store.schedule = schedules
        store.generation_running = False
        return {
            "status": "success",
            "count": len(schedules),
            "schedules": schedules
        }
    except Exception as e:
        store.generation_running = False
        raise HTTPException(status_code=500, detail=f"Scheduling error: {str(e)}")
@router.get("/progress")
def get_generator_progress():
    return {
        "count": store.generation_progess,
        "running": store.generation_running
    }