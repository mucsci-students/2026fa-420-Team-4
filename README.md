# Team^4 Course Scheduler

A web application for editing and validating course configurations, generating
schedules, and viewing or exporting them. The GUI uses **React 19, TypeScript,
and Vite**; the API uses **FastAPI** and the MUCSCI Scheduler library.

## Requirements and installation

Install Python 3.12 or newer, uv, Node.js
20.19+ (or 22.12+) and npm. From the repository root:

```bash
uv sync --all-groups
cd frontend
npm ci
cd ..
```

`uv sync --all-groups` installs the Python application and test dependencies.
`npm ci` installs the frontend dependencies from the lockfile.

## Run the application

The API and GUI run separately. Start each in its own terminal from the
repository root.

**Terminal 1 — FastAPI backend**

```bash
uv run uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — React/Vite frontend**

```bash
cd frontend
npm run dev
```

Open <http://localhost:3000>. Vite proxies `/api` requests to the backend at
`http://127.0.0.1:8000`; keep both processes running while using the app.

## Tests and frontend build

From the repository root, run the Python test suite:

```bash
uv run pytest
```

Build and type-check production frontend assets:

```bash
cd frontend
npm run build
```

Vite writes the built assets to `frontend/dist/`.

## Architecture (MVC-style)

The application separates state/data, presentation, and request/action handling
in an MVC-style structure:

- **Model:** `backend/models/session_store.py` holds the active configuration and
  schedule collection in memory. The scheduler library supplies configuration
  and schedule domain models.
- **View:** `frontend/view/` contains the React UI:
  `MainMenu.tsx`, `ConfigurationEditor.tsx`, `ScheduleGenerator.tsx`, and
  `ScheduleViewer.tsx`.
- **Controllers:** `frontend/view/front_controllers/` coordinates frontend
  actions; `backend/back_controllers/` implements FastAPI endpoints for
  configuration, generation, and schedule import/export.
- `frontend/view/api.ts` is the frontend API client. Python tests are in
  `tests/`.


## Using the three modes

The left menu switches among **Configuration Editor**,
**Schedule Generator**, and **Schedule Viewer**. The Configuration Editor can
also expand to show its data sections: Rooms, Labs, Courses, Faculty, Timeslots,
and Class Patterns.

**Representative workflow:** Create or load a configuration in the Configuration
Editor, add or edit its course and resource rows, validate and save it; load that
JSON in Schedule Generator, choose a limit and optimizer preferences, and
generate schedules; then open Schedule Viewer to navigate the available
schedules, switch between room/lab and faculty groupings, or load and export
schedule JSON.

### Configuration Editor

1. Choose **Create New Config** to start a `new-config.json`, or choose a JSON
   file to load an existing configuration.
2. Loading validates the JSON with the backend before opening it. Edit or add
   rows in the appropriate section; changes remain a local draft.
3. Draft validation runs as edits are committed. Review displayed validation
   errors, correct them, and select **Save Changes**. Saving validates again;
   only a valid configuration is downloaded.
4. Deleting a row requires confirmation. Deletion does not automatically update
   other items that refer to it. If a deletion leaves invalid references,
   validation reports the issue and saving does not download the invalid
   configuration; edit those references or restore the deleted item.

Unsaved edits are not written automatically. There is no discard/overwrite
confirmation when starting a new configuration or loading another one, so save
the draft before replacing it.

### Schedule Generator

1. Open **Schedule Generator**, choose a valid configuration JSON file, and
   review its load/validation status.
2. Set **Maximum schedules to generate** and choose any optimizer preferences
   The limit and flags are generation overrides for
   the loaded configuration.
3. Select **Generate Schedules**. The status area reports the result or error.
   Choose JSON or CSV in **Export format**, then select **Export Generated
   Schedules** to download the generated collection.

### Schedule Viewer

1. Open **Schedule Viewer** to load available schedules, or select **Load JSON
   Schedules** to import a schedule file.
2. Use the schedule selector and **Previous**/**Next** buttons to navigate
   schedules. Choose **View by Room / Lab** or **View by Faculty** to regroup
   the displayed meetings.
3. **Export Selected JSON** downloads the current schedule;
   **Export All JSON** downloads all of the schedules. 
   **Clear Schedules** removes the available collection.

The Generator offers JSON and CSV exports; the Viewer exports JSON.

## Schedule JSON format

A schedule object has a `schedule_id` and a `courses` (or `assignments`) array. Assignments identify a
course with `course`, `course_str`, `course_id`, or `section`, and contain a
non-empty `times` (or `meetings`) array. Each meeting has a non-empty `day`, a
`start`/`start_time` value (minutes after midnight or an `HH:MM` string), and a
positive integer `duration` in minutes. For example:

```json
[
  {
    "schedule_id": 1,
    "courses": [
      {
        "course_id": "CS101",
        "times": [
          { "day": "MON", "start": 540, "duration": 60 }
        ]
      }
    ]
  }
]
```


