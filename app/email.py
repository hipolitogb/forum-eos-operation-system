"""Send emails via Resend HTTP API (no SDK dependency — just urllib)."""
import json
import os
import urllib.request
import urllib.error

RESEND_API_URL = "https://api.resend.com/emails"

# Env var overrides DB value (ops escape hatch).
EMAIL_API_KEY_ENV = os.getenv("EMAIL_API_KEY", "")


def _api_key(settings) -> str:
    return EMAIL_API_KEY_ENV or (settings.email_api_key if settings else "")


def send_magic_link(settings, *, to_email: str, link: str) -> str | None:
    """Send a magic-link email. Returns None on success, or an error string."""
    api_key = _api_key(settings)
    if not api_key:
        return "Email API key not configured. Set it in /admin → Member authentication."

    forum_name = settings.forum_name or "Forum OS"
    from_name = settings.email_from_name or forum_name
    from_addr = settings.email_from_address or "onboarding@resend.dev"

    body = {
        "from": f"{from_name} <{from_addr}>",
        "to": [to_email],
        "subject": f"Sign in to {forum_name}",
        "html": (
            f"<div style='font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 0;'>"
            f"<p style='font-size:15px;color:#333;'>Hi,</p>"
            f"<p style='font-size:15px;color:#333;'>Click the button below to sign in to <strong>{forum_name}</strong>. "
            f"This link expires in 15 minutes.</p>"
            f"<p style='margin:24px 0;'>"
            f"<a href='{link}' style='display:inline-block;background:#F59E0B;color:#111;padding:12px 28px;"
            f"border-radius:6px;text-decoration:none;font-weight:600;font-size:15px;'>Sign in →</a>"
            f"</p>"
            f"<p style='font-size:13px;color:#888;'>Or copy this link:<br>"
            f"<a href='{link}' style='color:#888;word-break:break-all;'>{link}</a></p>"
            f"<p style='font-size:13px;color:#bbb;margin-top:32px;'>— {forum_name}</p>"
            f"</div>"
        ),
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        RESEND_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status < 300:
                return None
            return f"Resend returned HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
            return f"Resend error: {detail.get('message', str(e))}"
        except Exception:
            return f"Resend HTTP {e.code}"
    except Exception as e:
        return f"Failed to send email: {e}"


def send_test_email(settings, *, to_email: str) -> str | None:
    """Send a test email to verify config. Returns None on success, error str otherwise."""
    api_key = _api_key(settings)
    if not api_key:
        return "Email API key not configured."

    forum_name = settings.forum_name or "Forum OS"
    from_name = settings.email_from_name or forum_name
    from_addr = settings.email_from_address or "onboarding@resend.dev"

    body = {
        "from": f"{from_name} <{from_addr}>",
        "to": [to_email],
        "subject": f"Test email from {forum_name}",
        "html": f"<p>If you see this, email delivery from <strong>{forum_name}</strong> is working.</p>",
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        RESEND_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return None if resp.status < 300 else f"Resend returned HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
            return f"Resend error: {detail.get('message', str(e))}"
        except Exception:
            return f"Resend HTTP {e.code}"
    except Exception as e:
        return f"Failed: {e}"
