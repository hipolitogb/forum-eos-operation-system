# Forum Operating System

Lightweight operations dashboard for EO Forums (and any small peer-advisory group running EO-style meetings). Designed to live at a single URL that all forum members can open, with an admin area for the moderator.

## What it does

- **Parking Lot** — a living log of open threads, grouped per member. Drag-to-reorder, tag by type (Open, Deep Dive, Topical, Recurring, Improving), schedule Deep Dive dates.
- **Members** — the active forum roster, with optional roles (Chair, Moderator, etc.).
- **Agenda** — a standard retreat/meeting timeline for reference during sessions.
- **Constitution** — the forum's rules at a glance.
- **5% Reflections** — prompt and structure for the classic four-areas check-in.
- **Admin** — password-protected. Inline member CRUD, CSV backup/restore for members and parking items.

## Stack

- FastAPI + SQLAlchemy + Alembic
- Postgres 16
- htmx + Tailwind (CDN) + SortableJS
- Docker Compose

## Quick start (local dev)

```bash
git clone https://github.com/hipolitogb/forum-eos-operation-system.git
cd forum-eos-operation-system
cp .env.example .env
# edit .env — at minimum set ADMIN_PASSWORD
docker compose up -d --build
```

Open `http://localhost:8000` for the dashboard, `http://localhost:8000/admin` for the admin (HTTP Basic Auth — any username + `ADMIN_PASSWORD` from `.env`).

## Deploy to a VPS

The app is a self-contained Docker stack. Any VPS with Docker installed can host it:

1. Copy the repo to the server (e.g. `git clone` into `/home/apps/forum/`).
2. Create `.env` with production values. **Set a strong `ADMIN_PASSWORD` and `POSTGRES_PASSWORD`.**
3. `docker compose up -d --build`.
4. Put a reverse proxy (Caddy / nginx / Cloudflare Tunnel) in front of port `APP_PORT` to expose it on HTTPS.

The app writes:
- `backups/` — CSV snapshots (every manual backup + every pre-restore auto-backup).
- Postgres data — in the `forum_db_data` named volume (survives `docker compose down`; persists until you `docker volume rm`).

## Environment variables

See [`.env.example`](.env.example). Required for production:

| Var | Purpose |
|-----|---------|
| `ADMIN_PASSWORD` | Password for `/admin`. Anything — username ignored. |
| `POSTGRES_PASSWORD` | Postgres password. Must match `DATABASE_URL`. |
| `DATABASE_URL` | SQLAlchemy URL. Default wires to the `db` service. |
| `APP_PORT` | Host port exposed by Docker. Default `8000`. |

## Roadmap

- [ ] Editable branding from `/admin` (forum name, tagline, logo, fonts, colors)
- [ ] `install.sh` one-liner bootstrap
- [ ] Published Docker image on GHCR
- [ ] i18n (currently English only)

## License

MIT
