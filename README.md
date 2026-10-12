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

The backend and frontend run separately. Start each in separate terminals from the
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

Vite writes the built assets to `frontend/dist/`

## Architecture

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

### Screen-by-screen walkthrough

1. **Configuration Editor:** The left sidebar highlights the editor and lists
   its configuration sections. In the main pane, choose **Create New Config**
   or **Choose File**. After loading a valid JSON file, choose Rooms, Labs,
   Courses, Faculty, Timeslots, or Class Patterns in the sidebar; edit a row,
   add a row, or delete one. Applied edits remain a draft until **Save Changes**.
   Draft validation results appear above the save controls. If you try to load
   another file or create a new configuration with unsaved edits, confirm that
   you want to discard them; cancel to keep the current draft.
2. **Schedule Generator:** Select the sidebar's **Schedule Generator** mode.
   Its main pane presents the configuration file chooser, generation limit,
   optimizer checkboxes, **Generate Schedules**, and Generation Status. Load
   the configuration saved in step 1, choose the limit and optional optimizer
   preferences, then generate. The progress bar and schedule count update while
   work is in progress. Choose JSON or CSV before exporting. An invalid limit
   displays an inline error and disables generation; a limit of `0` asks for
   confirmation before clearing schedules.
3. **Schedule Viewer:** Select **Schedule Viewer** in the sidebar. Load schedule
   JSON if schedules are not already available. The top controls show the
   schedule count, file loading, selected/all JSON export, and clear action.
   Use the schedule selector or **Previous**/**Next**; below it, switch between
   **View by Room / Lab** and **View by Faculty**. **Clear Schedules** requires
   confirmation before removing the available collection.

### Configuration Editor

1. Choose **Create New Config** to start a `new-config.json`, or choose a JSON
   file to load an existing configuration.
2. Loading validates the JSON with the backend before opening it. Edit or add
   rows in the appropriate section; changes remain a local draft.
3. Draft validation runs as edits are applied. Review displayed validation
   errors, correct them, and select **Save Changes**. Saving validates again;
   only a valid configuration can be downloaded.
   Invalid configuration or draft data is shown in an error panel, and saving
   is blocked until it passes validation.
4. Deleting a row requires confirmation. Deletion does not automatically update
   other items that refer to it. If a deletion leaves invalid references,
   validation reports the issue and saving does not download the invalid
   configuration; edit those references or restore the deleted item.

Loading another file, creating a new configuration, or leaving/reloading the
page with unsaved edits triggers a confirmation. Choosing to keep editing
preserves the draft.

### Schedule Generator

1. Open **Schedule Generator**, choose a valid configuration JSON file, and
   review its load/validation status.
2. Set **Maximum schedules to generate** and choose any optimizer preferences
   (Faculty → Course, Faculty → Room, Faculty → Lab, Same Room, Same Lab,
   Pack Rooms, or Pack Labs). The limit must be a non-negative whole number
   within the safe integer range. Invalid values show an inline error and
   disable generation. A limit of `0` asks for confirmation before clearing
   schedules.
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
   **Export All JSON** downloads all of the schedules. Names follow
   `<originalfilename>_schedule<number>.json` and
   `<originalfilename>_allschedules.json`. The browser saves downloads to its
   configured location and handles repeated filenames according to its download
   settings. **Clear Schedules** asks for confirmation before removing the
   available collection.

The Generator offers JSON and CSV exports; the Viewer exports JSON.

### Unsaved drafts and destructive actions

Unsaved configuration edits are held in the editor until saved. Replacing the
configuration by loading a file or starting a new one, and leaving or reloading
the page, requires confirmation before discarding those edits. Deleting a
configuration row, clearing schedules in the Viewer, and using generation limit
`0` to clear schedules also require confirmation. Canceling any confirmation
leaves the current data unchanged.

## Schedule JSON format

A schedule object has a `schedule_id` and a `courses` array. `courses` identify a
course with `course`, `course_str`, `course_id`, or `section`, and contain a
non-empty `times` (or `meetings`) array. Each meeting has a non-empty `day`, a
`start`/`start_time` value, and a positive integer `duration` in minutes. For 
example:

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
