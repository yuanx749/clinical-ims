# Clinical Information Management System

A Django application for managing clinical patients, imaging records, and simple analytics.

## Stack

- Django 5.2 LTS
- SQLite for local development
- Bootstrap 5 for basic UI
- D3 for interactive analytics
- uv for dependency and virtual environment management

Bootstrap and D3 are loaded from CDN links in the templates; they are not vendored in this repository.

## Features

- Patient and scan pages require login.
- Users can change their password after signing in.
- Scan records can be searched across patients, reasons, and diagnoses.
- Scan image uploads are limited to PNG/JPEG files under 2 MB.
- Scan image files are removed when their records are deleted.
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
- Add, search, filter, view, edit, and delete scan records.
- Confirm scan uploads reject invalid files and dates.
- Change the signed-in user's password.
- Open Analytics and change the sex filter.
