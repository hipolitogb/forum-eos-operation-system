import csv
import io
import os
import re
import secrets
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, Response, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Member, ParkingItem
from app.branding import (
    branding_context,
    get_or_create_settings,
    DISPLAY_FONTS,
    BODY_FONTS,
    VALID_COLOR_RE,
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="ADMIN_PASSWORD not configured")
    if not secrets.compare_digest(credentials.password, ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


router = APIRouter(dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="app/templates")

BACKUP_DIR = Path("/app/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

VALID_TAGS = {"open", "deep-dive", "topical", "recurring", "improving"}

MEMBER_HEADERS = ["id", "name", "role", "display_order"]
PARKING_HEADERS = ["id", "person_name", "title", "tag", "deep_dive_date", "context", "display_order"]


def _export_members_csv(db: Session) -> str:
    rows = db.query(Member).order_by(Member.display_order).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(MEMBER_HEADERS)
    for m in rows:
        w.writerow([m.id, m.name, m.role or "", m.display_order or 0])
    return buf.getvalue()


def _export_parking_csv(db: Session) -> str:
    rows = db.query(ParkingItem).order_by(ParkingItem.person_name, ParkingItem.display_order).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(PARKING_HEADERS)
    for i in rows:
        w.writerow([i.id, i.person_name, i.title, i.tag, i.deep_dive_date or "", i.context or "", i.display_order or 0])
    return buf.getvalue()


def _persist_backup(db: Session, label: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = BACKUP_DIR / f"{ts}-{label}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "members.csv").write_text(_export_members_csv(db))
    (folder / "parking-lot.csv").write_text(_export_parking_csv(db))
    return folder


@router.get("")
def admin_page(request: Request, db: Session = Depends(get_db)):
    backups = []
    if BACKUP_DIR.exists():
        backups = sorted([p.name for p in BACKUP_DIR.iterdir() if p.is_dir()], reverse=True)[:20]
    members = db.query(Member).order_by(Member.display_order, Member.name).all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        **branding_context(db),
        "backups": backups,
        "members": members,
        "member_count": len(members),
        "parking_count": db.query(ParkingItem).count(),
    })


# ---------- Brand identity ----------

UPLOAD_DIR = Path("/app/app/static/uploads")
LOGO_MAX_BYTES = 1 * 1024 * 1024  # 1 MB
LOGO_ALLOWED_EXT = {"png": "png", "jpg": "jpg", "jpeg": "jpg", "svg": "svg"}


def _logo_ext_from_upload(file: UploadFile) -> str | None:
    ct = (file.content_type or "").lower()
    if ct == "image/png":
        return "png"
    if ct in ("image/jpeg", "image/jpg"):
        return "jpg"
    if ct in ("image/svg+xml", "image/svg"):
        return "svg"
    name = (file.filename or "").lower()
    for ext_hint, canonical in LOGO_ALLOWED_EXT.items():
        if name.endswith("." + ext_hint):
            return canonical
    return None


def _clear_existing_logos():
    if UPLOAD_DIR.exists():
        for canonical in set(LOGO_ALLOWED_EXT.values()):
            old = UPLOAD_DIR / f"logo.{canonical}"
            if old.exists():
                old.unlink()


@router.post("/brand")
async def brand_update(
    request: Request,
    db: Session = Depends(get_db),
    forum_name: str = Form(""),
    tagline: str = Form(""),
    display_font: str = Form(""),
    body_font: str = Form(""),
    color_primary: str = Form(""),
    color_secondary: str = Form(""),
    color_tertiary: str = Form(""),
    logo: UploadFile | None = File(None),
):
    errors: list[str] = []

    forum_name = (forum_name or "").strip()
    tagline = (tagline or "").strip()
    if not forum_name:
        errors.append("forum_name is required")
    if len(forum_name) > 100:
        errors.append("forum_name is too long (max 100)")
    if len(tagline) > 200:
        errors.append("tagline is too long (max 200)")

    if display_font not in DISPLAY_FONTS:
        errors.append(f"display_font invalid (allowed: {', '.join(DISPLAY_FONTS.keys())})")
    if body_font not in BODY_FONTS:
        errors.append(f"body_font invalid (allowed: {', '.join(BODY_FONTS.keys())})")

    for label, value in [("color_primary", color_primary), ("color_secondary", color_secondary), ("color_tertiary", color_tertiary)]:
        if not re.match(VALID_COLOR_RE, value or ""):
            errors.append(f"{label} must be a hex color like #F59E0B")

    if errors:
        return Response(
            status_code=400,
            content="<span class='text-red-400'>" + " · ".join(errors) + "</span>",
            media_type="text/html",
        )

    settings = get_or_create_settings(db)
    settings.forum_name = forum_name
    settings.tagline = tagline
    settings.display_font = display_font
    settings.body_font = body_font
    settings.color_primary = color_primary.upper()
    settings.color_secondary = color_secondary.upper()
    settings.color_tertiary = color_tertiary.upper()

    logo_msg = ""
    if logo is not None and (logo.filename or "").strip():
        ext = _logo_ext_from_upload(logo)
        if ext is None:
            return Response(
                status_code=400,
                content="<span class='text-red-400'>logo: unsupported file type (PNG, JPG or SVG only)</span>",
                media_type="text/html",
            )
        content = await logo.read()
        if len(content) > LOGO_MAX_BYTES:
            return Response(
                status_code=400,
                content=f"<span class='text-red-400'>logo: file too large (max {LOGO_MAX_BYTES // 1024} KB)</span>",
                media_type="text/html",
            )
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        _clear_existing_logos()
        dest = UPLOAD_DIR / f"logo.{ext}"
        dest.write_bytes(content)
        settings.logo_path = f"uploads/logo.{ext}"
        logo_msg = " · logo updated"

    db.commit()

    return Response(
        content=f"<span class='text-emerald-400'>✓ saved{logo_msg} — reloading…</span><script>setTimeout(()=>location.reload(), 600);</script>",
        media_type="text/html",
    )


@router.post("/brand/logo/clear")
def brand_logo_clear(db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)
    settings.logo_path = ""
    _clear_existing_logos()
    db.commit()
    return Response(
        content="<span class='text-emerald-400'>✓ logo removed — reloading…</span><script>setTimeout(()=>location.reload(), 600);</script>",
        media_type="text/html",
    )


@router.get("/backup")
def backup_download(db: Session = Depends(get_db)):
    folder = _persist_backup(db, label="manual")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("members.csv", (folder / "members.csv").read_text())
        zf.writestr("parking-lot.csv", (folder / "parking-lot.csv").read_text())
    zip_buf.seek(0)

    filename = f"forum-backup-{folder.name}.zip"
    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _validate_members_csv(text_: str) -> tuple[list[dict], list[str]]:
    errors = []
    reader = csv.DictReader(io.StringIO(text_))
    missing = [h for h in ["name"] if h not in (reader.fieldnames or [])]
    if missing:
        return [], [f"members.csv: missing required columns: {missing}"]

    rows = []
    seen_ids = set()
    for idx, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        if not name:
            errors.append(f"members.csv line {idx}: empty 'name'")
            continue
        id_str = (row.get("id") or "").strip()
        id_val = None
        if id_str:
            try:
                id_val = int(id_str)
                if id_val in seen_ids:
                    errors.append(f"members.csv line {idx}: duplicate id {id_val}")
                seen_ids.add(id_val)
            except ValueError:
                errors.append(f"members.csv line {idx}: id '{id_str}' is not an integer")
        order_str = (row.get("display_order") or "0").strip() or "0"
        try:
            order = int(order_str)
        except ValueError:
            errors.append(f"members.csv line {idx}: display_order '{order_str}' is not an integer")
            order = 0
        rows.append({
            "id": id_val,
            "name": name,
            "role": (row.get("role") or "").strip(),
            "display_order": order,
        })
    return rows, errors


def _validate_parking_csv(text_: str, member_names: set[str]) -> tuple[list[dict], list[str]]:
    errors = []
    warnings = []
    reader = csv.DictReader(io.StringIO(text_))
    required = ["person_name", "title", "tag"]
    missing = [h for h in required if h not in (reader.fieldnames or [])]
    if missing:
        return [], [f"parking-lot.csv: missing required columns: {missing}"]

    rows = []
    seen_ids = set()
    for idx, row in enumerate(reader, start=2):
        person = (row.get("person_name") or "").strip()
        title = (row.get("title") or "").strip()
        tag = (row.get("tag") or "open").strip()
        if not person:
            errors.append(f"parking-lot.csv line {idx}: empty 'person_name'")
        if not title:
            errors.append(f"parking-lot.csv line {idx}: empty 'title'")
        if tag not in VALID_TAGS:
            errors.append(f"parking-lot.csv line {idx}: tag '{tag}' invalid (must be one of {sorted(VALID_TAGS)})")

        id_str = (row.get("id") or "").strip()
        id_val = None
        if id_str:
            try:
                id_val = int(id_str)
                if id_val in seen_ids:
                    errors.append(f"parking-lot.csv line {idx}: duplicate id {id_val}")
                seen_ids.add(id_val)
            except ValueError:
                errors.append(f"parking-lot.csv line {idx}: id '{id_str}' is not an integer")

        order_str = (row.get("display_order") or "0").strip() or "0"
        try:
            order = int(order_str)
        except ValueError:
            errors.append(f"parking-lot.csv line {idx}: display_order '{order_str}' is not an integer")
            order = 0

        if person and person != "Group" and person not in member_names:
            warnings.append(f"parking-lot.csv line {idx}: '{person}' does not match any member (orphan group will be created)")

        rows.append({
            "id": id_val,
            "person_name": person,
            "title": title,
            "tag": tag,
            "deep_dive_date": (row.get("deep_dive_date") or "").strip(),
            "context": (row.get("context") or "").strip(),
            "display_order": order,
        })
    return rows, errors + [f"WARN: {w}" for w in warnings]


def _parse_upload(file: UploadFile) -> str:
    content = file.file.read()
    if isinstance(content, bytes):
        return content.decode("utf-8-sig")
    return content


def _upload_has_content(file: UploadFile | None) -> bool:
    return bool(file and file.filename)


@router.post("/restore/preview")
async def restore_preview(
    request: Request,
    db: Session = Depends(get_db),
    members_file: UploadFile | None = File(None),
    parking_file: UploadFile | None = File(None),
):
    has_members = _upload_has_content(members_file)
    has_parking = _upload_has_content(parking_file)

    if not has_members and not has_parking:
        return templates.TemplateResponse("partials/restore_preview.html", {
            "request": request,
            "errors": ["You must upload at least one CSV (members.csv or parking-lot.csv)."],
            "has_blocking": True,
            "has_members": False,
            "has_parking": False,
        })

    members_text = _parse_upload(members_file) if has_members else ""
    parking_text = _parse_upload(parking_file) if has_parking else ""

    members_rows, member_errors = ([], [])
    if has_members:
        members_rows, member_errors = _validate_members_csv(members_text)

    parking_rows, parking_errors = ([], [])
    if has_parking:
        if has_members:
            member_names = {m["name"] for m in members_rows}
        else:
            member_names = {m.name for m in db.query(Member).all()}
        parking_rows, parking_errors = _validate_parking_csv(parking_text, member_names)

    all_errors = member_errors + parking_errors
    has_blocking = any(not e.startswith("WARN:") for e in all_errors)

    return templates.TemplateResponse("partials/restore_preview.html", {
        "request": request,
        "errors": all_errors,
        "has_blocking": has_blocking,
        "has_members": has_members,
        "has_parking": has_parking,
        "members_count_new": len(members_rows),
        "parking_count_new": len(parking_rows),
        "members_count_cur": db.query(Member).count(),
        "parking_count_cur": db.query(ParkingItem).count(),
        "members_text": members_text,
        "parking_text": parking_text,
    })


@router.post("/restore/apply")
async def restore_apply(
    request: Request,
    db: Session = Depends(get_db),
    members_text: str = Form(""),
    parking_text: str = Form(""),
    apply_members: str = Form(""),
    apply_parking: str = Form(""),
):
    do_members = apply_members == "1"
    do_parking = apply_parking == "1"

    if not do_members and not do_parking:
        return JSONResponse({"ok": False, "errors": ["Nothing to apply."]}, status_code=400)

    members_rows, member_errors = ([], [])
    if do_members:
        members_rows, member_errors = _validate_members_csv(members_text)

    parking_rows, parking_errors = ([], [])
    if do_parking:
        if do_members:
            member_names = {m["name"] for m in members_rows}
        else:
            member_names = {m.name for m in db.query(Member).all()}
        parking_rows, parking_errors = _validate_parking_csv(parking_text, member_names)

    all_errors = [e for e in (member_errors + parking_errors) if not e.startswith("WARN:")]
    if all_errors:
        return JSONResponse({"ok": False, "errors": all_errors}, status_code=400)

    _persist_backup(db, label="pre-restore")

    if do_members and do_parking:
        db.execute(text("TRUNCATE members, parking_items RESTART IDENTITY CASCADE"))
    elif do_members:
        db.execute(text("TRUNCATE members RESTART IDENTITY CASCADE"))
    elif do_parking:
        db.execute(text("TRUNCATE parking_items RESTART IDENTITY CASCADE"))

    if do_members:
        for m in members_rows:
            db.add(Member(
                id=m["id"],
                name=m["name"],
                role=m["role"],
                display_order=m["display_order"],
            ))
    if do_parking:
        for p in parking_rows:
            db.add(ParkingItem(
                id=p["id"],
                person_name=p["person_name"],
                title=p["title"],
                tag=p["tag"],
                deep_dive_date=p["deep_dive_date"],
                context=p["context"],
                display_order=p["display_order"],
            ))
    db.flush()

    if do_members:
        max_member = max((m["id"] or 0 for m in members_rows), default=0)
        if max_member:
            db.execute(text(f"SELECT setval('members_id_seq', {max_member}, true)"))
    if do_parking:
        max_parking = max((p["id"] or 0 for p in parking_rows), default=0)
        if max_parking:
            db.execute(text(f"SELECT setval('parking_items_id_seq', {max_parking}, true)"))

    db.commit()

    return JSONResponse({
        "ok": True,
        "members_imported": len(members_rows) if do_members else None,
        "parking_imported": len(parking_rows) if do_parking else None,
    })


# ---------- Member CRUD for admin UI ----------

@router.get("/members/rows")
def admin_members_rows(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.display_order, Member.name).all()
    return templates.TemplateResponse("partials/admin_member_rows.html", {
        "request": request,
        "members": members,
    })


@router.get("/members/new")
def admin_member_new(request: Request):
    return templates.TemplateResponse("partials/admin_member_form.html", {
        "request": request,
        "member": None,
    })


@router.get("/members/{member_id}/edit")
def admin_member_edit(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = db.query(Member).get(member_id)
    if not member:
        return Response(status_code=404)
    return templates.TemplateResponse("partials/admin_member_form.html", {
        "request": request,
        "member": member,
    })


@router.get("/members/{member_id}")
def admin_member_row(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = db.query(Member).get(member_id)
    if not member:
        return Response(status_code=404)
    return templates.TemplateResponse("partials/admin_member_row.html", {
        "request": request,
        "member": member,
    })


@router.post("/members")
def admin_member_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    role: str = Form(""),
    display_order: int = Form(0),
):
    name = name.strip()
    if not name:
        return Response(status_code=400, content="name required")
    member = Member(name=name, role=role.strip(), display_order=display_order)
    db.add(member)
    db.commit()
    db.refresh(member)
    members = db.query(Member).order_by(Member.display_order, Member.name).all()
    return templates.TemplateResponse("partials/admin_member_rows.html", {
        "request": request,
        "members": members,
    })


@router.post("/members/{member_id}")
def admin_member_update(
    member_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    role: str = Form(""),
    display_order: int = Form(0),
):
    member = db.query(Member).get(member_id)
    if not member:
        return Response(status_code=404)
    name = name.strip()
    if not name:
        return Response(status_code=400, content="name required")
    member.name = name
    member.role = role.strip()
    member.display_order = display_order
    db.commit()
    db.refresh(member)
    return templates.TemplateResponse("partials/admin_member_row.html", {
        "request": request,
        "member": member,
    })


@router.delete("/members/{member_id}")
def admin_member_delete(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).get(member_id)
    if member:
        db.delete(member)
        db.commit()
    return Response(status_code=200, content="")
