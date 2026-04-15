"""Branding helpers: load settings, derive color shades, build font URLs."""
from sqlalchemy.orm import Session
from app.models import (
    ForumSettings,
    AgendaItem,
    ConstitutionPillar,
    ConstitutionRule,
    ReflectionArea,
)


# Curated font lists exposed in the admin dropdowns. The key is the human
# name stored in the DB; the value is the Google Fonts URL fragment (family
# name with weights as needed).
DISPLAY_FONTS: dict[str, str] = {
    "Alfa Slab One": "Alfa+Slab+One",
    "Bungee": "Bungee",
    "Bebas Neue": "Bebas+Neue",
    "Staatliches": "Staatliches",
    "Abril Fatface": "Abril+Fatface",
    "Fraunces": "Fraunces:wght@900",
    "Oswald": "Oswald:wght@700",
    "Archivo Black": "Archivo+Black",
}

BODY_FONTS: dict[str, str] = {
    "Manrope": "Manrope:wght@300;400;500;600;700;800",
    "Inter": "Inter:wght@300;400;500;600;700;800",
    "DM Sans": "DM+Sans:wght@300;400;500;700",
    "IBM Plex Sans": "IBM+Plex+Sans:wght@300;400;500;600;700",
}

VALID_COLOR_RE = r"^#[0-9A-Fa-f]{6}$"


def get_or_create_settings(db: Session) -> ForumSettings:
    """Return the singleton settings row, creating defaults if missing."""
    settings = db.query(ForumSettings).filter_by(id=1).one_or_none()
    if settings is None:
        settings = ForumSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = (hex_color or "#000000").lstrip("#")
    if len(h) != 6:
        return (0, 0, 0)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02X}{max(0, min(255, g)):02X}{max(0, min(255, b)):02X}"


def darken(hex_color: str, amount: float = 0.2) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount)))


def lighten(hex_color: str, amount: float = 0.35) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount),
    )


def rgb_csv(hex_color: str) -> str:
    """Returns an rgb triplet like '245, 158, 11' for use in rgba() calls."""
    r, g, b = _hex_to_rgb(hex_color)
    return f"{r}, {g}, {b}"


def google_fonts_url(display_font: str, body_font: str) -> str:
    families = []
    d = DISPLAY_FONTS.get(display_font, DISPLAY_FONTS["Alfa Slab One"])
    b = BODY_FONTS.get(body_font, BODY_FONTS["Manrope"])
    families.append(d)
    families.append(b)
    families.append("JetBrains+Mono:wght@400;500")
    params = "&".join(f"family={f}" for f in families)
    return f"https://fonts.googleapis.com/css2?{params}&display=swap"


def branding_context(db: Session) -> dict:
    """Returns a dict ready to merge into Jinja template contexts."""
    settings = get_or_create_settings(db)
    return {
        "settings": settings,
        "brand": {
            "primary_rgb": rgb_csv(settings.color_primary),
            "secondary_rgb": rgb_csv(settings.color_secondary),
            "tertiary_rgb": rgb_csv(settings.color_tertiary),
            "primary_soft": lighten(settings.color_primary, 0.35),
            "primary_deep": darken(settings.color_primary, 0.20),
            "secondary_deep": darken(settings.color_secondary, 0.20),
            "google_fonts_url": google_fonts_url(settings.display_font, settings.body_font),
        },
        "display_fonts": list(DISPLAY_FONTS.keys()),
        "body_fonts": list(BODY_FONTS.keys()),
    }


def forum_content_context(db: Session) -> dict:
    """Dynamic content rendered on the home page: agenda, constitution,
    5% reflections. All editable from /admin."""
    return {
        "agenda": db.query(AgendaItem).order_by(AgendaItem.display_order, AgendaItem.id).all(),
        "pillars": db.query(ConstitutionPillar).order_by(ConstitutionPillar.display_order, ConstitutionPillar.id).all(),
        "rules": db.query(ConstitutionRule).order_by(ConstitutionRule.display_order, ConstitutionRule.id).all(),
        "reflection_areas": db.query(ReflectionArea).order_by(ReflectionArea.display_order, ReflectionArea.id).all(),
    }
