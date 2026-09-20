# 2026fa-420-Team-4 Course Scheduler

## Overview

A Python-based scheduling program for making department schedules.

## Features

- Create or Load  an existing configuration file
- Modify rooms, labs, courses, and faculty
- Validate schedule configuration data
- Generate possible schedules from the config file

## Project Structure

```text
.
├── shell.py
├── config_commands.py
├── room_commands.py
├── lab_commands.py
├── course_commands.py
├── faculty_commands.py
├── schedulertest.py
├── example.json
├── minimal_config.json
├── README.md
├── LICENSE
```

## Requirements
You should Installl the latest version of python

This project uses the external scheduler library from:

https://github.com/mucsci/scheduler

Install it before running this project:

```bash
pip install course-constraint-scheduler
```

## Installation

1. Clone the repository.
2. Open a terminal in the project.
3. Run the shell:

```bash
python shell.py
```

## Configuration

The project stores schedule information in JSON:

```json
{
  "config": {
    "rooms": [],
    "labs": [],
    "courses": [],
    "faculty": []
  },
  "time_slot_config": {
    "times": {
      "MON": [],
      "TUE": [],
      "WED": [],
      "THU": [],
      "FRI": []
    },
    "classes": []
  },
  "limit": 0,
  "optimizer_flags": []
}
```

## License

This project is licensed under the repository license included in the project files.
