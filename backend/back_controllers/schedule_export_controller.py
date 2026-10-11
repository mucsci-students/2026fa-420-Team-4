from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend import ScheduleExporter
from backend.models.session_store import store

router = APIRouter(prefix="/api/schedule", tags=["Schedule Export"])


def _export_schedule(extension: str) -> Response:
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
        store.config_filename, extension
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
    return _export_schedule(".json")


@router.get("/export/csv")
def export_schedule_csv() -> Response:
    return _export_schedule(".csv")
