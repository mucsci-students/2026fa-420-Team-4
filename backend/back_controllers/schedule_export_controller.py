from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from backend import ScheduleExporter
from backend import Schedule_importer
from backend.models.session_store import store

router = APIRouter(prefix="/api/schedule", tags=["Schedule Export"])


@router.get("/available")
def get_available_schedules() -> dict:
    """Return stored schedules, their count, and the source filename, if known."""
    schedules = store.schedule or []
    return {
        "count": len(schedules),
        "schedules": schedules,
        "source_filename": store.schedule_filename or store.config_filename,
    }


@router.post("/import")
async def import_schedule_file(file: UploadFile = File(...)) -> dict:
    """Validate an uploaded JSON export and replace stored schedules and filename.

    Raise HTTP 400 for invalid input without replacing the existing schedules.
    """
    try:
        schedules = Schedule_importer.load_schedules(
            await file.read(), file.filename or ""
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    store.schedule = schedules
    store.schedule_filename = file.filename
    return {
        "count": len(schedules),
        "schedules": schedules,
        "source_filename": store.schedule_filename,
    }


@router.delete("/available")
def clear_available_schedules() -> dict:
    """Clear stored schedules and their source filename, returning an empty collection."""
    store.schedule = []
    store.schedule_filename = None
    return {"count": 0, "schedules": [], "source_filename": None}


def _export_schedule(extension: str) -> Response:
    """Build a JSON or CSV attachment using the schedule or configuration filename.

    Raise HTTP 400 when schedules are absent or HTTP 500 if serialization fails.
    """
    if not store.schedule:
        raise HTTPException(
            status_code=400,
            detail="No generated schedules are available to export.",
        )

    try:
        if extension == ".json":
            content = ScheduleExporter.schedules_to_json(store.schedule)
            media_type = "application/json; charset=utf-8"
        else:
            content = ScheduleExporter.schedules_to_csv(store.schedule)
            media_type = "text/csv; charset=utf-8"
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not export generated schedules: {error}",
        ) from error

    filename = ScheduleExporter.schedule_export_filename(
        store.schedule_filename or store.config_filename, extension
    )
    if filename.isascii():
        content_disposition = f'attachment; filename="{filename}"'
    else:
        content_disposition = f"attachment; filename*=UTF-8''{quote(filename)}"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition},
    )


@router.get("/export/json")
def export_schedule_json() -> Response:
    """Return stored schedules as a downloadable JSON attachment."""
    return _export_schedule(".json")


@router.get("/export/csv")
def export_schedule_csv() -> Response:
    """Return stored schedules as a downloadable CSV attachment."""
    return _export_schedule(".csv")
