# Forum OS

Operations dashboard for EO forums and peer-advisory groups. Members-only parking lot, meeting agenda, constitution, and 5% reflections — all editable, fully branded, runs as a single Docker stack.

---

## Launch your forum in 5 minutes

No coding required. You'll need a GitHub account and a credit card for [Railway](https://railway.com) ($5/month after free trial).

### Step 1 — Create a Railway project

1. Go to [railway.com](https://railway.com) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select **hipolitogb/forum-eos-operation-system** (you may need to fork it first)
4. Railway starts building — takes about 2 minutes

### Step 2 — Add a database

In your Railway project dashboard, click **+ Add Service → Database → PostgreSQL**.

### Step 3 — Connect the database to the app

1. Click on your **app service** (the one that's NOT Postgres)
2. Go to the **Variables** tab
3. Click **+ New Variable** → Name: `DATABASE_URL` → Value: click **Insert Reference** → select `DATABASE_URL` from the Postgres service
4. The app redeploys automatically

### Step 4 — Open your forum and follow the setup wizard

Railway gives you a public URL (e.g. `forum-os-production.up.railway.app`). Open it.

The app detects it's a fresh install and starts a **5-step setup wizard**:

1. **Your forum** — name, tagline, logo upload
2. **Look & feel** — pick 3 colors and fonts
3. **Secure your admin** — set username, password, and recovery email (replaces the default `admin / admin`)
4. **Members** — add forum members with their email addresses
5. **Email & auth** — paste your Resend API key and choose whether to require member login

Every step has a **Skip** button if you want to configure it later. When you finish, you land on your fully configured dashboard.

### Step 5 — Set up email login (if you skipped it in the wizard)

To lock your forum so only members can access it, you need a [Resend](https://resend.com) account (free — 3000 emails/month):

1. Go to [resend.com](https://resend.com) → create an account → get an API key
2. In your forum, go to `/admin` → sign in → scroll to **Member authentication**
3. Paste the Resend API key, set a "From" address, and toggle **Require login for members**

Members sign in by entering their email and clicking the magic link they receive. Sessions last 30 days.

### Step 6 — Custom domain (optional)

In Railway: **Settings → Networking → Custom Domain** → enter your domain → follow the DNS instructions. Railway provides automatic HTTPS.

---

## Self-host on your own server

If you prefer a VPS (Hetzner, DigitalOcean, etc.) with Docker installed:

```bash
curl -sSL https://raw.githubusercontent.com/hipolitogb/forum-eos-operation-system/main/install.sh | bash
```

This pulls the pre-built image from GHCR, generates random passwords, starts the stack, and prints the URL. Open the URL and the setup wizard starts automatically.

Put a reverse proxy (Caddy / Cloudflare Tunnel / nginx) in front of `APP_PORT` to serve over HTTPS.

Tunables: `INSTALL_DIR=/srv/forum APP_PORT=8080 bash install.sh`

---

## Admin panel

After setup, the admin panel lives at `/admin`. It has a proper login form (not a browser popup) with username + password.

**Forgot your password?** Click "Forgot password?" on the login page. If you configured a recovery email during setup, you'll receive a reset link. If not, set `ADMIN_PASSWORD=yourpass` in your `.env` file and restart — this env var works as a fallback login.

---

## What's editable from /admin

| Section | What you can change |
|---------|-------------------|
| Brand identity | Forum name, tagline, logo, 3 colors, display + body fonts |
| Admin credentials | Username, password (bcrypt-hashed), recovery email |
| Members | Name, email, role, display order |
| Agenda | Meeting timeline items (time, title, duration, description) |
| Constitution · Pillars | Core principles cards |
| Constitution · Rules | Rules table (topic + rule) |
| 5% Reflections | Intro text, life-area cards (emoji, label, color), closing note |
| Member authentication | Toggle login requirement, Resend API key, from address |
| Backup / Restore | Download/upload members + parking lot as CSV |

---

## Stack

- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL 16
- **Frontend**: htmx + Tailwind CSS (CDN) + SortableJS
- **Auth**: bcrypt (admin) + HMAC-SHA256 signed cookies (members + admin sessions) + Resend magic links
- **Deploy**: Docker image on GHCR (multi-arch amd64 + arm64)

---

## Environment variables

All optional — the app runs with sensible defaults. Configure via Railway's Variables tab, or in `.env` for self-hosted.

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://forum:forum@db:5432/forum` |
| `APP_PORT` | Host port (self-hosted only) | `8000` |
| `ADMIN_PASSWORD` | Fallback admin password (env overrides DB) | — |
| `EMAIL_API_KEY` | Resend API key (env overrides DB) | — |

---

## License

MIT — free to use, modify, and distribute.
