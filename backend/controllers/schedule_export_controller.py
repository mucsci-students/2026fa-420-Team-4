from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend import ScheduleExporter
from backend.models.session_store import store

router = APIRouter(prefix="/api/schedule", tags=["Schedule Export"])


@router.get("/export/csv")
def export_schedule_csv():
    if not store.schedule:
        raise HTTPException(
            status_code=400,
            detail="No generated schedules are available to export.",
        )

    try:
        csv_content = ScheduleExporter.schedules_to_csv(store.schedule)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not export generated schedules: {error}",
        ) from error

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="schedules.csv"'},
    )
