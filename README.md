# DGS Website Backend

Django backend for the DGS website. The project follows the feature-app structure used by the ET ERP monolith while keeping this service focused on DGS website content, enquiries, and page analytics.

## Technology

- Python 3.12
- Django 5.1
- SQLite
- Local media storage by default

## Project structure

| Path | Purpose |
| --- | --- |
| `manage.py` | Django management command entry point |
| `config/` | Project settings, URL routing, and WSGI/ASGI entry points |
| `backend/people/` | People shown on the website |
| `backend/projects/` | Projects, brochures, photographs, and nearby amenities/places |
| `backend/channel_partners/` | Channel partner onboarding records |
| `backend/analytics/` | Per-page visit counters and visit logs |
| `backend/careers/` | Job applications submitted through the website |
| `backend/requirements/` | Shared, production, and test Python dependencies |
| `files/` | Uploaded media in local development (ignored by Git) |

Each domain app owns its models, admin registrations, tests, and migrations. Models follow the ET ERP convention of `created` and `modified` audit timestamps and explicit `Meta` verbose names. File fields use Django's storage API and app-specific upload paths. Local uploads are stored under `files/`; configure a production storage backend through Django's `STORAGES` setting before deploying.

## Data models

- **Person** — name, title, and description.
- **Project** — name, short and long descriptions, budget, status, location, and optional brochure/video links.
- **ProjectConfiguration** — per-project BHK option, area, bed/bath counts, and optional layout image.
- **ProjectPhoto** — title and file, linked to a project.
- **ProjectAmenity** — project amenities and optional images.
- **ProjectAmenityPlace** — nearby places with category, coordinates, and distance, linked to a project.
- **ChannelPartner** — name, phone number, email, optional type, and creation timestamp. The type choices are intentionally not fixed yet.
- **PageAnalytics** — one visit counter per page. `record_visit()` increments the counter atomically and creates a corresponding log entry.
- **PageAnalyticsLog** — page, visit count at the time of the visit, optional IP address, and creation timestamp.
- **JobApplication** — applicant name, email, mobile number, job title, and message/description.

Channel partner type choices and analytics requirements can be extended once those details are agreed.

## People API

- `GET /api/people/get-people-list/?role=founder` or `?role=director` returns a list containing each person's `name` and `title`.
- `GET /api/people/get-people-details/?person_id=<id>` returns one person's `name`, `title`, and `description`.

These read-only endpoints are public and do not require authentication. The list endpoint requires `role` to be `founder` or `director`.

## Projects API

- `GET /api/projects/get-project-list/` returns six project cards per page. Use `page=1`, `page=2`, etc. for the "show more" flow. The response includes `count`, `next_page`, `previous_page`, and `results`.
- Optional list filters: `status` (`Completed`, `OnGoing`, or `Upcoming`), `location`, `min_price`, `max_price`, and `bhk`.
- `search_term` matches project name, location, price (including terms such as `2.89 Cr` or `89 Lacs`), or BHK (such as `2 BHK`).
- `GET /api/projects/get-project-details/?project_id=<id>` returns the project detail data: descriptions, status, price, address/map link, photos, room configurations, amenities, neighborhood places, brochure, and video/tour links.

These read-only endpoints are public and do not require authentication.

## Local development

Create and activate a Python 3.12 virtual environment named `venv`, matching the ET ERP backend setup:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/common.txt
```

On macOS or Linux, activate it with `source venv/bin/activate`. To install the optional production or test dependencies, use `python -m pip install -r backend/requirements/prod.txt` or `python -m pip install -r backend/requirements/test.txt`.

The project uses SQLite, so you do not need to install or start PostgreSQL. The database file is `db.sqlite3` in the project root by default. Its filename can be set with `DB_NAME` in `.env`. Django loads `.env` automatically, and the file is ignored by Git.

The relevant settings are:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Development-only key | Django secret key; set a strong secret outside local development |
| `DJANGO_DEBUG` | `true` | Enable Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed host names |
| `DB_NAME` | `db.sqlite3` | SQLite database filename, relative to the project root |
| `DJANGO_MEDIA_ROOT` | `files/` | Local upload directory |

Create database tables and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

The Django admin is available at `/admin/`. Create an administrator with:

```powershell
python manage.py createsuperuser
```

When `DEBUG` is enabled, uploaded files are served from `/files/` by Django's development server. Do not use this media serving configuration in production.

## Migrations

After changing a model, generate and apply migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Tests

Run the app tests with Django's test runner:

```powershell
python manage.py test
```

Alternatively, install the test requirements and run pytest:

```powershell
python -m pip install -r backend/requirements/test.txt
pytest -v
```

## Production notes

- - Use Python 3.12 and install the pinned dependencies from `backend/requirements/prod.txt`.
- Set a private `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and an explicit `DJANGO_ALLOWED_HOSTS`.
- Ensure the SQLite database file is on persistent storage and included in your backup plan.
- Configure a durable media storage backend (for example, S3-compatible storage) before accepting production uploads.
- Run migrations as part of deployment and serve the application with a production WSGI/ASGI server.
