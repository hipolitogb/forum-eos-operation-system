"""First-run setup wizard. Lives under /setup/* so it inherits
the admin router's Basic Auth dependency."""
import re

import bcrypt
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Member, AdminUser
from app.branding import branding_context, get_or_create_settings, DISPLAY_FONTS, BODY_FONTS, VALID_COLOR_RE
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

TOTAL_STEPS = 5
UPLOAD_DIR = __import__("pathlib").Path("/app/app/static/uploads")
LOGO_MAX = 1 * 1024 * 1024


def _logo_ext(file: UploadFile) -> str | None:
    ct = (file.content_type or "").lower()
    if ct == "image/png": return "png"
    if ct in ("image/jpeg", "image/jpg"): return "jpg"
    if ct in ("image/svg+xml", "image/svg"): return "svg"
    return None


def _ctx(request, db, step, extra=None):
    ctx = {
        "request": request,
        **branding_context(db),
        "step": step,
        "total_steps": TOTAL_STEPS,
        "display_fonts": list(DISPLAY_FONTS.keys()),
        "body_fonts": list(BODY_FONTS.keys()),
        "members": db.query(Member).order_by(Member.display_order).all(),
        "admin_user": db.query(AdminUser).filter_by(id=1).one_or_none(),
    }
    if extra:
        ctx.update(extra)
    return ctx


@router.get("")
def setup_index(db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)
    if settings.setup_completed:
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/setup/1", status_code=303)


@router.get("/{step}")
def setup_step(step: int, request: Request, db: Session = Depends(get_db)):
    settings = get_or_create_settings(db)
    if settings.setup_completed:
        return RedirectResponse("/", status_code=303)
    step = max(1, min(step, TOTAL_STEPS))
    return templates.TemplateResponse("setup.html", _ctx(request, db, step))


# ---------- Step 1: Forum name + tagline + logo ----------

@router.post("/1")
async def setup_save_1(
    request: Request,
    db: Session = Depends(get_db),
    forum_name: str = Form(""),
    tagline: str = Form(""),
    logo: UploadFile | None = File(None),
):
    settings = get_or_create_settings(db)
    settings.forum_name = (forum_name or "").strip() or "FORUM OS"
    settings.tagline = (tagline or "").strip()

    if logo and (logo.filename or "").strip():
        ext = _logo_ext(logo)
        if ext:
            content = await logo.read()
            if len(content) <= LOGO_MAX:
                UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
                for old_ext in ("png", "jpg", "svg"):
                    p = UPLOAD_DIR / f"logo.{old_ext}"
                    if p.exists(): p.unlink()
                (UPLOAD_DIR / f"logo.{ext}").write_bytes(content)
                settings.logo_path = f"uploads/logo.{ext}"

    db.commit()
    return RedirectResponse("/setup/2", status_code=303)


# ---------- Step 2: Colors + fonts ----------

@router.post("/2")
def setup_save_2(
    request: Request,
    db: Session = Depends(get_db),
    display_font: str = Form(""),
    body_font: str = Form(""),
    color_primary: str = Form(""),
    color_secondary: str = Form(""),
    color_tertiary: str = Form(""),
):
    settings = get_or_create_settings(db)
    if display_font in DISPLAY_FONTS:
        settings.display_font = display_font
    if body_font in BODY_FONTS:
        settings.body_font = body_font
    if re.match(VALID_COLOR_RE, color_primary or ""):
        settings.color_primary = color_primary.upper()
    if re.match(VALID_COLOR_RE, color_secondary or ""):
        settings.color_secondary = color_secondary.upper()
    if re.match(VALID_COLOR_RE, color_tertiary or ""):
        settings.color_tertiary = color_tertiary.upper()
    db.commit()
    return RedirectResponse("/setup/3", status_code=303)


# ---------- Step 3: Admin credentials ----------

@router.post("/3")
def setup_save_3(
    request: Request,
    db: Session = Depends(get_db),
    new_username: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
):
    new_username = (new_username or "").strip()
    new_password = (new_password or "").strip()
    if new_username and new_password and len(new_password) >= 6 and new_password == confirm_password:
        user = db.query(AdminUser).filter_by(id=1).one_or_none()
        if user:
            user.username = new_username
            user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            db.commit()
    return RedirectResponse("/setup/4", status_code=303)


# ---------- Step 4: Members ----------

@router.post("/4")
def setup_add_member(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    email: str = Form(""),
    role: str = Form(""),
):
    name = (name or "").strip()
    if name:
        max_order = db.query(Member).count()
        db.add(Member(
            name=name,
            email=(email or "").strip().lower() or None,
            role=(role or "").strip(),
            display_order=max_order + 1,
        ))
        db.commit()
    return RedirectResponse("/setup/4", status_code=303)


@router.post("/4/delete/{member_id}")
def setup_delete_member(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).get(member_id)
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse("/setup/4", status_code=303)


# ---------- Step 5: Email & auth ----------

@router.post("/5")
def setup_save_5(
    request: Request,
    db: Session = Depends(get_db),
    auth_enabled: str = Form(""),
    email_api_key: str = Form(""),
    email_from_address: str = Form(""),
    email_from_name: str = Form(""),
):
    settings = get_or_create_settings(db)
    settings.auth_enabled = auth_enabled == "1"
    settings.email_api_key = (email_api_key or "").strip()
    settings.email_from_address = (email_from_address or "").strip() or "onboarding@resend.dev"
    settings.email_from_name = (email_from_name or "").strip()
    settings.setup_completed = True
    db.commit()
    return RedirectResponse("/", status_code=303)
