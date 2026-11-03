# DGS Website Backend

Django backend for the DGS website. The project follows the feature-app structure used by the ET ERP monolith while keeping this service focused on DGS website content, enquiries, and page analytics.

## Technology

- Python 3.12
- Django 5.1
- SQLite for local development; PostgreSQL when `expound_POSTGRES_URL` is set
- Local media storage by default; S3-compatible storage when `S3_ENDPOINT_URL` is set

## Project structure

| Path | Purpose |
| --- | --- |
| `manage.py` | Django management command entry point |
| `config/settings/` | Settings split like the ET ERP backend: `common.py` (shared), `dev.py` and `prod.py` |
| `config/` | URL routing and WSGI/ASGI entry points |
| `backend/geo/` | Six chained location levels (`Location1` to `Location6`), as in the ET ERP `geo` app |
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
- **Location1 to Location6** — six chained levels (for example country, state, district, city, area). Each level points at its parent. Manage them in the admin.
- **Project** — name, short and long descriptions, budget, status, an `is_featured` flag, location, and optional brochure/video links. `price_budget` is the text shown on the website (for example `₹ 2.89 Cr Onwards`); `starting_price` is the amount in rupees parsed from it on every save, and is what price filters and search use (it is empty when the text has no number). `location_1` to `location_6` optionally link the project to the location levels; a level must belong to the level above it.
- **ProjectConfiguration** — per-project BHK option, area, bed/bath counts, and optional layout image.
- **ProjectPhoto** — title and file, linked to a project.
- **ProjectAmenity** — project amenities with an optional description and image.
- **ProjectAmenityPlace** — nearby places with category, coordinates, and distance, linked to a project.
- **ChannelPartner** — name, phone number, email, optional type, and creation timestamp. The type choices are intentionally not fixed yet.
- **PageAnalytics** — one visit counter per page. `record_visit()` increments the counter atomically and creates a corresponding log entry.
- **PageAnalyticsLog** — page, visit count at the time of the visit, optional IP address, and creation timestamp.
- **JobApplication** — applicant name, email, mobile number, job title, and message/description.

Channel partner type choices and analytics requirements can be extended once those details are agreed.

## People API

- `GET /api/people/get-people-list/?role=founder` or `?role=director` returns a list containing each person's `id`, `name`, `title`, `description`, and `image`.
- `GET /api/people/get-people-details/?person_id=<id>` returns one person's `name`, `title`, `description`, and `image`.

These read-only endpoints are public and do not require authentication. The list endpoint requires `role` to be `founder` or `director`.

## Projects API

- `GET /api/projects/get-project-list/` returns six project cards per page. Use `page=1`, `page=2`, etc. for the "show more" flow. The response includes `count`, `next_page`, `previous_page`, and `results`.
- Optional list filters: `status` (`Completed`, `OnGoing`, or `Upcoming`), `featured` (`true` or `1` returns only featured projects), `location`, `location_1` to `location_6`, `min_price`, `max_price`, and `bhk`.
- `location` is text and matches the project's location name, address, or the name of any of its six locations. `location_1` to `location_6` take a location ID.
- `min_price` and `max_price` are amounts in rupees (for example `5000000`) compared with the project's `starting_price`. Projects whose price text has no number are left out when either is used.
- `search_term` matches project name, location (including the six location names), price text, a price in words or numbers (for example `2.89 Cr`, `289 Lakh`, or `89 Lacs`), or BHK (such as `2 BHK`).
- `GET /api/projects/get-place-list/` returns the places (location 5, for example Andheri) that have projects, most projects first, as `{count, results}`. `count` is the total number of places; each result has `id`, `name`, `image_url`, and `project_count`. `?limit=5` keeps only the top five (the home page's "Choose from 05+ places in Mumbai"). Use a place `id` as `location_5` in the project list to filter by it. A place's image is set in the admin (Location5).
- `GET /api/projects/get-project-details/?project_id=<id>` returns the project detail data: descriptions, status, price, `is_featured`, `location_1` to `location_6` (each `{id, name}` or `null`), address/map link, photos, room configurations, amenities, neighborhood places, brochure, and video/tour links.

These read-only endpoints are public and do not require authentication.

## Local development

Create and activate a Python 3.12 virtual environment named `venv`, matching the ET ERP backend setup:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/common.txt
```

On macOS or Linux, activate it with `source venv/bin/activate`. To install the optional production or test dependencies, use `python -m pip install -r backend/requirements/prod.txt` or `python -m pip install -r backend/requirements/test.txt`.

Without `expound_POSTGRES_URL` the project uses SQLite, so you do not need to install or start PostgreSQL. The database file is `db.sqlite3` in the project root. Django loads `.env` automatically, and the file is ignored by Git.

### Settings: dev and prod

Settings live in `config/settings/`, like the ET ERP backend: `common.py` holds what every environment shares, and `dev.py` and `prod.py` add what differs. `DJANGO_CONFIGURATION` picks one:

| | `manage.py` | `wsgi.py` / `asgi.py` (gunicorn) |
| --- | --- | --- |
| Not set | `dev` | `prod` |
| `DJANGO_CONFIGURATION=development` | `dev` | `dev` |
| `DJANGO_CONFIGURATION=production` | `prod` | `prod` |

So local work needs no setup: `python manage.py ...` runs the development settings. The server entry points default to production, so forgetting the variable can never start a debug server. On a server, set `DJANGO_CONFIGURATION=production` for **every** command, including `migrate` and `collectstatic`.

| | `dev.py` | `prod.py` |
| --- | --- | --- |
| `DEBUG` | on | off |
| `ALLOWED_HOSTS` | any | `DJANGO_ALLOWED_HOSTS` (required) |
| Secret key | `DJANGO_SECRET_KEY`, else a development-only key | `DJANGO_SECRET_KEY` (required; the older name `expound` is still read) |
| Database | SQLite, or PostgreSQL if `expound_POSTGRES_URL` is set | the same, with SSL required for PostgreSQL |
| Proxies (`NUM_PROXIES`) | 0 | `DJANGO_NUM_PROXIES`, default 1 |

`prod.py` refuses to start if the secret key or allowed hosts are missing. `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated `https://` origins) is needed to log in to the admin over HTTPS behind a proxy.

**CORS:** every website, including `localhost` on any port, may call `/api/` from a browser, as in the ET ERP backend (`CORS_ALLOW_ALL_ORIGINS`). That is safe here because the API is public and cookie-free; the admin is not covered.

Other variables: `DJANGO_MEDIA_ROOT` (upload directory, default `files/`), and the optional `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION`, `SUPABASE_PROJECT_REF` for S3-compatible media storage.

Create database tables and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

Restart `runserver` completely (stop it, then start it again) after the settings change; an already running server keeps the old settings.

The Django admin is available at `/admin/`. Create an administrator with:

```powershell
python manage.py createsuperuser
```

In development (`DEBUG` on), uploaded files are served from `/files/` by Django's development server. Do not use this media serving configuration in production.

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

- Use Python 3.12 and install the pinned dependencies from `backend/requirements/prod.txt`.
- Set `DJANGO_CONFIGURATION=production` on the server, for the web process and for every `manage.py` command.
- Set a private `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`; the app will not start without them. Set `DJANGO_CSRF_TRUSTED_ORIGINS` if you log in to the admin over HTTPS behind a proxy.
- Set `DJANGO_NUM_PROXIES` to the number of reverse proxies in front of the app (`0` if gunicorn is exposed directly).
- Use PostgreSQL through `expound_POSTGRES_URL`. If you use SQLite instead, keep the database file on persistent storage and include it in your backup plan.
- Configure a durable media storage backend (for example, S3-compatible storage) before accepting production uploads.
- On each deployment run `python manage.py migrate` and `python manage.py collectstatic --noinput`. Migrations create the table that stores the API throttle counters; WhiteNoise then serves the collected admin static files.
- Serve the application with a production WSGI/ASGI server such as gunicorn.
