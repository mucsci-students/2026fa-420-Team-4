"""Export one schedule from the scheduler library as JSON or CSV."""

import argparse
import csv
import json
import sys
from pathlib import Path


# Convert supported scheduler objects into plain mappings for serialization.
def _schedule_dict(schedule):
    if isinstance(schedule, dict):
        return schedule
    for method in ("model_dump", "to_dict"):
        converter = getattr(schedule, method, None)
        if callable(converter):
            return converter()
    if hasattr(schedule, "__dict__"):
        return {key: value for key, value in vars(schedule).items() if not key.startswith("_")}
    raise TypeError("The selected schedule cannot be converted to a mapping")


# Find the requested schedule through the package's direct lookup methods or
# by searching its available schedule collection.
def _get_schedule(schedule_id):
    """Look up exactly one schedule through the scheduler package."""
    try:
        import scheduler
    except ImportError as exc:
        raise RuntimeError("Install the scheduler library to export schedules") from exc

    for method_name in ("get_schedule", "load_schedule", "find_schedule"):
        method = getattr(scheduler, method_name, None)
        if callable(method):
            result = method(schedule_id)
            if result is not None:
                return result

    collection = getattr(scheduler, "schedules", None)
    if callable(collection):
        collection = collection()
    if collection is not None:
        matches = []
        for item in collection:
            data = _schedule_dict(item)
            identifier = data.get("id", data.get("schedule_id"))
            if str(identifier) == str(schedule_id):
                matches.append(item)
        if len(matches) == 1:
            return matches[0]
    raise LookupError(f"Could not find schedule {schedule_id!r}")


# Write one schedule as JSON or CSV, inferring the format from the output
# extension unless the caller supplies an explicit format.
def export_schedule(schedule_id, output_file, file_format=None):
    """Export one schedule to a JSON or CSV file."""
    schedule = _schedule_dict(_get_schedule(schedule_id))
    path = Path(output_file)
    kind = (file_format or path.suffix.lstrip(".")).lower()

    if kind == "json":
        path.write_text(json.dumps(schedule, indent=2, default=str) + "\n", encoding="utf-8")
    elif kind == "csv":
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(schedule))
            writer.writeheader()
            writer.writerow({
                key: json.dumps(value, default=str) if isinstance(value, (dict, list)) else value
                for key, value in schedule.items()
            })
    else:
        raise ValueError("Choose JSON or CSV, or provide an output filename with .json or .csv")
    return path


# Parse CLI options, perform the export, and report success or a user-facing
# error while returning the corresponding process status.
def main(argv=None):
    parser = argparse.ArgumentParser(description="Export a single schedule as JSON or CSV")
    parser.add_argument("schedule_id", help="ID of the schedule to export")
    parser.add_argument("output", help="Destination filename (.json or .csv)")
    parser.add_argument("--format", choices=("json", "csv"), help="Override the filename extension")
    args = parser.parse_args(argv)
    try:
        destination = export_schedule(args.schedule_id, args.output, args.format)
    except (LookupError, RuntimeError, TypeError, ValueError, OSError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1
    print(f"Exported schedule to {destination}")
    return 0


# Keep command-line execution separate from importing this module as a library.
if __name__ == "__main__":
    raise SystemExit(main())