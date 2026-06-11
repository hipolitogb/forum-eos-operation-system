# MEMORY.md — Forum OS

## Qué es

Dashboard de operaciones para foros EO: parking lot, agenda, constitución, 5% reflections. FastAPI + Postgres + htmx, deploy en Railway (auto-deploy al pushear a `main` en GitHub → `hipolitogb/forum-eos-operation-system`).

## Estado actual (2026-06-11)

- Producción corre en Railway. **No hay Railway CLI linkeado en esta máquina ni URL/credenciales de prod guardadas localmente** — para backups de datos de prod hay que usar `/admin → Backup` desde el browser, o linkear Railway CLI.
- Dev local: `docker compose up` con `.env` (puerto 8010). El volumen `forum_db_data` conserva datos de dev viejos.
- Último cambio: **cerrar tópicos de parking lot** (commit de hoy):
  - Columna `closed` (Integer 0/1) en `parking_items` — migración alembic `008`.
  - Ruta `PUT /parking/{id}/toggle-closed` en `app/routes/parking.py`.
  - `parking_item.html`: ítem cerrado se ve gris (opacity-50, tachado, chip "Closed"), sin drag handle ni botón edit; botón ↺ Reopen. Ítem abierto tiene botón ✓ Close.
  - Backup/restore CSV: columna `closed` agregada al export; el import la acepta opcional (CSVs viejos sin la columna importan con closed=0).

## Decisiones de arquitectura

- `closed` es Integer 0/1 (no Boolean) para matchear el estilo del resto del schema (`auth_enabled`).
- Ítems cerrados no se pueden editar ni arrastrar, pero sí borrar y reabrir. Siguen contando en el contador del grupo.
- Antes de cambios con migración: tag git de backup (`backup-pre-closed-topics` quedó pusheado para este cambio).

## Cómo verificar localmente

```bash
docker compose up -d --build   # app en :8010, corre alembic upgrade head solo
docker exec forum-db psql -U forum -d forum -c "\d parking_items"
```

Primera visita redirige al setup wizard; para saltarlo en dev: `UPDATE forum_settings SET setup_completed=true`.

## Pendientes

- No hay test suite automatizada (verificación manual con gstack /browse).
- Conseguir/guardar la URL de prod y considerar linkear Railway CLI para poder hacer `pg_dump` antes de migraciones futuras.
