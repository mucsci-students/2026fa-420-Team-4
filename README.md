# Team^4 Course Scheduler



## Overview

A web application interface for generating, validating, and managing course schedules.

The application uses a FastAPI backend and a Vite + React + TypeScript frontend, powered by MUCSCI Scheduler

---
## Prerequisites

Requires:

* **Python 3.12+**
* **uv**
* **Node.js 18+**
* **npm**

Python dependencies are managed through `uv`.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/mucsci-students/2026fa-420-Team-4.git
cd 2026fa-420-Team-4
```

### 2. Sync the Python environment

```bash
python -m uv sync
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

# Running the Application

The web application requires the FastAPI backend and React frontend to run simultaneously.

## Terminal 1 — FastAPI Backend

From the repository root:

```bash
python -m uv run uvicorn backend.main:app --reload --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```
---

## Terminal 2 — React + Vite Frontend

From the repository root:

```bash
cd frontend
npm run dev
```

The interactive GUI will be available at:

```text
http://localhost:3000
```
## Project Structure

```text
.
├── backend/                   # FastAPI backend & legacy command modules
│   ├── controllers/           # API endpoints (/api/config, /api/generator)
│   ├── models/                # Session store state management
│   ├── json_validator.py      # JSON schema & diagnostic validator
│   ├── main.py                # FastAPI entry point
│   ├── __commands.py          # Shell Commands
│   └── shell.py               # Interactive CLI shell
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── api.ts             # Axios API client
│   │   ├── App.tsx            # Control Dashboard interface
│   │   └── main.tsx           # React DOM root
│   ├── vite.config.ts         # Vite server proxy configuration
│   └── package.json
├── tests/                     # Unit tests & JSON fixture files
│   └── jsonfiles/             # Test JSON configurations
├── pyproject.toml             # Project configuration & dependencies
├── uv.lock                    # Locked dependency versions
└── README.md
```

