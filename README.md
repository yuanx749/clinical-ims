# Clinical Information Management System

A Django application for managing clinical patients, imaging records, and simple analytics.

## Stack

- Django 5.2 LTS
- SQLite for local development
- Bootstrap 5 for basic UI
- D3 for interactive analytics
- uv for dependency and virtual environment management

## Features

- Patient and scan pages require login.
- Scan image uploads are limited to PNG/JPEG files under 2 MB.
- Patient deletion is restricted to staff users.
- Scan edit and delete actions are restricted to the clinician who created the scan.
- D3 charts read authenticated JSON endpoints.
- Sample records and scan images can be generated locally.

## Local Setup

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py load_sample_data
uv run python manage.py runserver
```

The sample data command creates a clinician account:

- Username: `docy`
- Password: `V7qN4pX9rL2m`

Open `http://127.0.0.1:8000` and sign in.

## Testing

```bash
uv run python manage.py test
```

Manual checks:

- Create, edit, search, and delete patients.
- Add, view, edit, and delete scan records.
- Confirm scan uploads reject invalid files and dates.
- Open Analytics and change the sex filter.
