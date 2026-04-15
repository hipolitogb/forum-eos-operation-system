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

## Quick install (one command)

On any server with Docker + Docker Compose:

```bash
curl -sSL https://raw.githubusercontent.com/hipolitogb/forum-eos-operation-system/main/install.sh | bash
```

This pulls the pre-built image from GHCR, generates strong random passwords for you, and starts the stack. When it finishes, it prints your dashboard URL and admin credentials.

Tunables (set before running):

```bash
INSTALL_DIR=/srv/forum APP_PORT=8080 bash install.sh
```

After install, put a reverse proxy (Caddy / Cloudflare Tunnel / nginx) in front of `APP_PORT` to serve over HTTPS.

## Local dev (from source)

If you want to hack on the code:

```bash
git clone https://github.com/hipolitogb/forum-eos-operation-system.git
cd forum-eos-operation-system
cp .env.example .env
# edit .env — at minimum set ADMIN_PASSWORD
docker compose up -d --build
```

Open `http://localhost:8000` for the dashboard, `http://localhost:8000/admin` for the admin (HTTP Basic Auth — any username + `ADMIN_PASSWORD` from `.env`).

## Where data lives

- `backups/` — CSV snapshots (every manual backup + every pre-restore auto-backup).
- `uploads/` — user-uploaded logos (only in the installed stack; in dev they live in `app/static/uploads/`).
- Postgres data — in the named volume `forum_db_data` (survives `docker compose down`; persists until you `docker volume rm`).

## Environment variables

See [`.env.example`](.env.example). Required for production:

| Var | Purpose |
|-----|---------|
| `ADMIN_PASSWORD` | Password for `/admin`. Anything — username ignored. |
| `POSTGRES_PASSWORD` | Postgres password. Must match `DATABASE_URL`. |
| `DATABASE_URL` | SQLAlchemy URL. Default wires to the `db` service. |
| `APP_PORT` | Host port exposed by Docker. Default `8000`. |

## Roadmap

- [x] Editable branding from `/admin` (forum name, tagline, logo, fonts, colors)
- [x] `install.sh` one-liner bootstrap
- [x] Published Docker image on GHCR (multi-arch, amd64 + arm64)
- [ ] i18n (currently English only)
- [ ] Per-member onboarding questionnaire

## License

MIT
