from collections import OrderedDict
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Member, ParkingItem
from fastapi.responses import RedirectResponse
from app.branding import branding_context, forum_content_context
from app.routes.login import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _group_items_by_member_order(items, members):
    """Group parking items by person_name, in the order members are defined
    (display_order). Items referencing a non-member (e.g. 'Group') appear last,
    in insertion order."""
    ordered_names = [m.name for m in members]
    groups = OrderedDict()
    for name in ordered_names:
        person_items = [i for i in items if i.person_name == name]
        if person_items:
            groups[name] = person_items
    for item in items:
        if item.person_name not in groups:
            groups[item.person_name] = [i for i in items if i.person_name == item.person_name]
    return groups


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)

    members = db.query(Member).order_by(Member.display_order).all()
    items = db.query(ParkingItem).order_by(ParkingItem.display_order).all()
    groups = _group_items_by_member_order(items, members)

    tag_labels = {
        "open": "Open",
        "deep-dive": "Deep Dive",
        "topical": "Topical",
        "recurring": "Recurring",
        "improving": "Improving",
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        **branding_context(db),
        **forum_content_context(db),
        "members": members,
        "parking_groups": groups,
        "tag_labels": tag_labels,
        "all_tags": list(tag_labels.keys()),
        "member_names": [m.name for m in members] + ["Group"],
        "current_user_email": user if user != "*" else None,
    })
