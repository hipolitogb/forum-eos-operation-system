# Forum OS

Operations dashboard for EO forums and peer-advisory groups. Members-only parking lot, meeting agenda, constitution, and 5% reflections — all editable from the admin panel, fully branded, runs as a single Docker stack.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.app/new/template?template=https://github.com/hipolitogb/forum-eos-operation-system)

---

## Launch your forum in 5 minutes

No coding required. You'll need a GitHub account and a credit card for Railway ($5/month after free trial).

### Step 1 — Deploy to Railway

Click the **Deploy on Railway** button above. Sign in with GitHub when prompted. Railway creates your project and starts building — takes about 2 minutes.

### Step 2 — Add a database

In your Railway project dashboard, click **+ Add Service → Database → PostgreSQL**. Railway auto-links it to your app. Wait for the app to redeploy (~1 min).

### Step 3 — Connect DATABASE_URL

After adding Postgres, Railway creates a `DATABASE_URL` variable automatically in the Postgres service. You need to share it with the app:

1. Click on your **app service** (the one that's NOT Postgres)
2. Go to the **Variables** tab
3. Click **+ New Variable** → Name: `DATABASE_URL` → Value: click **Insert Reference** → select `DATABASE_URL` from the Postgres service
4. The app redeploys automatically

### Step 4 — Open your forum

Railway gives you a public URL (e.g. `forum-os-production.up.railway.app`). Click it.

- **Dashboard**: your forum URL
- **Admin panel**: your forum URL + `/admin`
- **Default login**: username `admin`, password `admin`

A red banner warns you to change the default password immediately.

### Step 5 — Set up your forum

In `/admin`:

1. **Change admin password** — top of the page, enter current (`admin`) + new credentials
2. **Brand it** — upload your logo, set name, tagline, pick colors and fonts
3. **Add members** — name, email, role (Chair, Moderator, etc.)
4. **Edit content** — agenda, constitution pillars & rules, 5% reflections

All changes save instantly — no deploy or restart needed.

### Step 6 — Enable member login (recommended)

By default the forum is open (anyone with the URL can see it). To lock it down:

**Get a Resend API key** (free — 3000 emails/month):
1. Go to [resend.com](https://resend.com) and create an account
2. In the Resend dashboard → API Keys → Create API Key → copy it

**Configure in your forum:**
1. In `/admin`, scroll to **Member authentication**
2. Paste the Resend API key
3. Set "From address" (use `onboarding@resend.dev` for testing, or verify your domain in Resend for a custom address)
4. Click **Send test email** to verify it works
5. Toggle **Require login for members** → Save

Now members sign in by entering their email and clicking the magic link they receive.

### Step 7 — Custom domain (optional)

In Railway: **Settings → Networking → Custom Domain** → enter your domain → follow the DNS instructions. Railway provides automatic HTTPS.

---

## Self-host on your own server

If you prefer a VPS (Hetzner, DigitalOcean, etc.) with Docker installed:

```bash
curl -sSL https://raw.githubusercontent.com/hipolitogb/forum-eos-operation-system/main/install.sh | bash
```

This pulls the pre-built image from GHCR, generates random passwords, starts the stack, and prints the URL + admin credentials. See `install.sh --help` for tunables (`INSTALL_DIR`, `APP_PORT`).

Put a reverse proxy (Caddy / Cloudflare Tunnel / nginx) in front of `APP_PORT` to serve over HTTPS.

---

## What's editable from /admin

| Section | What you can change |
|---------|-------------------|
| Brand identity | Forum name, tagline, logo, 3 colors, display + body fonts |
| Admin credentials | Username + bcrypt-hashed password |
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
- **Auth**: bcrypt (admin) + HMAC-SHA256 signed cookies (members) + Resend magic links
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
