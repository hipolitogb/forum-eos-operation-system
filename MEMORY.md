# MEMORY.md — Forum OS

## Qué es

Dashboard de operaciones para foros EO: parking lot, agenda, constitución, 5% reflections. FastAPI + Postgres + htmx. Repo: `hipolitogb/forum-eos-operation-system`.

## Producción (desde 2026-06-11)

- **https://pollos.hipolitogb.com** — Hetzner (`ssh hetzner`), detrás de Cloudflare Access + tunnel.
- Código en `/home/apps/forum` (clone de este repo), app en puerto **8006** (el tunnel apunta ahí — no tocar el puerto).
- La base reusa el directorio de datos del stack viejo: `/home/apps/data/postgres-pollos` (bind mount vía `docker-compose.override.yml`, untracked en el server). Credenciales en `.env` del server (user/db `pollos`).
- **Deploy**: commit + push acá, después `ssh hetzner "cd /home/apps/forum && git pull && docker compose up -d --build app"`. Antes de migraciones: `ssh hetzner "cd /home/apps/forum && docker compose exec -T db pg_dump -U pollos -Fc pollos" > backups/pre-X.dump`.
- **Rollback**: el stack viejo quedó intacto en `/home/apps/pollos` (repo `RobertoGonzalez/eo-pollos-hermanos`, su `parking-app/deploy.sh` documenta el flujo anterior). Backup pre-migración: `backups/pre-migracion-20260611-185334.{dump,sql}` en esta máquina.
- Railway NO se usa para esta instancia (el README describe Railway para terceros que deployen su propio foro).

## Historia de la migración (2026-06-11)

El sitio publicado venía del repo viejo `eo-pollos-hermanos/parking-app` (migración alembic `001` solamente). Este repo comparte ese mismo `001`, así que el cutover fue: clonar repo nuevo → apuntar al mismo data dir → `alembic upgrade head` aplicó 002→008 sin tocar datos (8 members, 30 parking items verificados). Tras el switch la app pide el **setup wizard** (`/setup/1`) — branding + admin user; el wizard no pisa members existentes.

## Último cambio de feature

**Cerrar tópicos de parking lot** (migración `008`):
- Columna `closed` (Integer 0/1) en `parking_items`; ruta `PUT /parking/{id}/toggle-closed`.
- Ítem cerrado: gris (opacity-50, tachado, chip "Closed"), sin drag ni edit; botones ↺ Reopen y borrar. Ítem abierto: botón ✓ Close en hover.
- Backup/restore CSV incluye columna `closed`; CSVs viejos sin la columna importan con closed=0.

## Decisiones de arquitectura

- `closed` es Integer 0/1 (no Boolean) para matchear el estilo del schema (`auth_enabled`).
- Cerrados no se editan ni arrastran, pero sí se borran/reabren; cuentan en el contador del grupo.
- Antes de cambios con migración: backup pg_dump + tag git (`backup-pre-closed-topics` quedó pusheado).

## Cómo verificar localmente

```bash
docker compose up -d --build   # app en :8010 (.env local), corre alembic upgrade head solo
docker exec forum-db psql -U forum -d forum -c "\d parking_items"
```

Primera visita redirige al setup wizard; para saltarlo en dev: `UPDATE forum_settings SET setup_completed=true`.

## Pendientes

- Hipólito tiene que completar el setup wizard en https://pollos.hipolitogb.com (branding, admin user, members ya están).
- No hay test suite automatizada (verificación manual con gstack /browse).
- Considerar portar el `deploy.sh` del repo viejo (backup obligatorio + deploy en un comando) a este repo.
