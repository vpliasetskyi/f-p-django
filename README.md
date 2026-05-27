# Cinemix

A personal cinematic library where users curate custom lists of movies and TV shows, track their watching status, and share their taste with others.

---

## Features

- **Search & Discovery** - Live TMDB search with filters (type, year, country, genre, rating, actor). Discover pre-curated categories: Hot Releases, Anime, Legendary TV, and more.
- **Content Detail Pages** - Full detail view with backdrop, cast, genres, tagline, runtime, community rating, and an official trailer popup (YouTube).
- **Status Tracking** - Mark any title as Plan to Watch, Watching, or Completed. Rate it 1–10 with an interactive star picker. Changes save instantly via HTMX - no page reload.
- **Custom Lists** - Create unlimited named lists. Search TMDB directly inside the list editor, add items instantly, edit custom posters and titles per item.
- **Social Sharing** - Make any custom list public and share it via Twitter/X, Facebook, or a copy link. Public lists are viewable without an account.
- **Profile Pages** - View stats (watched count, average rating), tracking history, and import another user's public list into your own account.

---

## Architecture

```
cinemix/
├── apps/
│   ├── content/        # ContentItem model, TMDB API service, detail + discover views
│   ├── lists/          # WatchItem, CustomList, CustomListItem models + all list views
│   └── users/          # CustomUser, Profile, auth views, signals
├── config/             # Django settings, URL root, WSGI
├── templates/
│   ├── base.html       # Full cx-* design system embedded as <style> block
│   ├── components/     # Navbar, search dropdown
│   ├── content/        # Home, detail, discover pages + HTMX partials
│   ├── lists/          # My lists, custom list editor/detail, public list, partials
│   └── users/          # Profile, edit profile
├── docker-compose.yml  # Local dev stack
├── Dockerfile          # Multi-stage build (builder + runtime)
└── pyproject.toml      # Dependencies managed by uv
```

### Data flow

```
Browser → Nginx (prod) → Gunicorn → Django views
                                         │
                          ┌──────────────┴──────────────┐
                          │                             │
                     PostgreSQL                    TMDB API v3
                  (users, lists,              (search, details,
                   watch items)               credits, trailers,
                                               discover)
```

### Key design decisions

- **No JS build step** - Alpine.js and HTMX loaded from CDN. All interactivity is server-driven partials or lightweight client state.
- **Custom CSS only** - A `cx-*` design token system (~500 lines) embedded directly in `base.html`. No Tailwind, no DaisyUI, no external stylesheet requests.
- **TMDB as source of truth** - Content detail data (genres, cast, backdrop, trailer) is fetched live on each page load, not stored in the database.
- **Through model for list items** - `CustomListItem` sits between `CustomList` and `ContentItem`, allowing per-item custom poster and title overrides within a list.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Framework | Django 6 (class-based views) |
| Database | PostgreSQL 16 |
| App server | Gunicorn |
| Interactivity | HTMX + Alpine.js (CDN) |
| Styling | Custom `cx-*` CSS system (embedded, no build step) |
| External API | TMDB API v3 |
| Package manager | uv (`pyproject.toml` + `uv.lock`) |
| Containers | Docker + Docker Compose |

---

## Local Development

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Clone the repo
git clone https://github.com/your-username/cinemix.git
cd cinemix

# 2. Create your .env file
cp .env.example .env
# Fill in SECRET_KEY, DATABASE_URL, TMDB_API_KEY

# 3. Start the stack
docker compose up --build

# 4. Run migrations (in a separate terminal)
docker compose exec web python manage.py migrate

# 5. Create a superuser (optional)
docker compose exec web python manage.py createsuperuser
```

App runs at `http://localhost:8000`

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for local dev, `False` in production |
| `DATABASE_URL` | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `TMDB_API_KEY` | API key from [themoviedb.org](https://www.themoviedb.org/settings/api) |
