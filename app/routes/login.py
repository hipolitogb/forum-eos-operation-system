from urllib.parse import quote

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.branding import branding_context, get_or_create_settings
from app.auth import (
    create_login_token,
    consume_login_token,
    is_member_email,
    rate_limit_ok,
    sign_session,
    verify_session,
    _get_or_generate_secret,
)
from app.email import send_magic_link

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COOKIE_NAME = "forum_session"


def get_current_user(request: Request, db: Session) -> str | None:
    """Return the email of the authenticated user, or None. Does NOT
    enforce — callers decide whether to redirect."""
    settings = get_or_create_settings(db)
    if not settings.auth_enabled:
        return "*"
    cookie = request.cookies.get(COOKIE_NAME)
    if not cookie:
        return None
    secret = _get_or_generate_secret(db)
    return verify_session(cookie, secret)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db), error: str = Query("")):
    settings = get_or_create_settings(db)
    if not settings.auth_enabled:
        return RedirectResponse("/", status_code=303)
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {
        "request": request,
        **branding_context(db),
        "error": error,
    })


@router.post("/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(""),
):
    settings = get_or_create_settings(db)
    if not settings.auth_enabled:
        return RedirectResponse("/", status_code=303)

    email = (email or "").lower().strip()

    if not email:
        return RedirectResponse("/login?error=" + quote("Please enter your email."), status_code=303)

    if not is_member_email(db, email):
        return RedirectResponse("/login?error=" + quote("No member with that email. Contact your moderator."), status_code=303)

    if not rate_limit_ok(email):
        return RedirectResponse("/login?error=" + quote("Too many requests. Try again in a few minutes."), status_code=303)

    ip = request.client.host if request.client else ""
    token = create_login_token(db, email, requester_ip=ip)

    base_url = str(request.base_url).rstrip("/")
    link = f"{base_url}/login/verify?token={token}"

    err = send_magic_link(settings, to_email=email, link=link)
    if err:
        return RedirectResponse("/login?error=" + quote(f"Could not send email: {err}"), status_code=303)

    return templates.TemplateResponse("login_sent.html", {
        "request": request,
        **branding_context(db),
        "email": email,
    })


@router.get("/login/verify")
def login_verify(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Query(""),
):
    settings = get_or_create_settings(db)

    if not token:
        return RedirectResponse("/login?error=" + quote("Missing token."), status_code=303)

    email = consume_login_token(db, token)
    if email is None:
        return RedirectResponse("/login?error=" + quote("Link expired or already used. Request a new one."), status_code=303)

    secret = _get_or_generate_secret(db)
    session_cookie = sign_session(email, secret)

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        session_cookie,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


@router.get("/logout")
def logout(request: Request):
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
