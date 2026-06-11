import json
from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ParkingItem, Member
from app.routes.pages import _group_items_by_member_order

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

TAG_LABELS = {
    "open": "Open",
    "deep-dive": "Deep Dive",
    "topical": "Topical",
    "recurring": "Recurring",
    "improving": "Improving",
}


def _ctx(request, db):
    members = db.query(Member).order_by(Member.display_order).all()
    return {
        "request": request,
        "tag_labels": TAG_LABELS,
        "all_tags": list(TAG_LABELS.keys()),
        "member_names": [m.name for m in members] + ["Group"],
    }


@router.get("")
def get_section(request: Request, db: Session = Depends(get_db)):
    return _render_section(request, db)


@router.put("/reorder")
def reorder(request: Request, db: Session = Depends(get_db), ids: str = Form("")):
    try:
        id_list = json.loads(ids)
    except (json.JSONDecodeError, TypeError):
        return Response(status_code=400)

    for idx, item_id in enumerate(id_list):
        item = db.query(ParkingItem).get(int(item_id))
        if item:
            item.display_order = idx + 1
    db.commit()
    return Response(status_code=204)


@router.get("/section")
def get_section_alias(request: Request, db: Session = Depends(get_db)):
    return _render_section(request, db)


@router.get("/{item_id}")
def get_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(ParkingItem).get(item_id)
    return templates.TemplateResponse("partials/parking_item.html", {**_ctx(request, db), "item": item})


@router.get("/{item_id}/edit")
def edit_form(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(ParkingItem).get(item_id)
    return templates.TemplateResponse("partials/parking_item_edit.html", {**_ctx(request, db), "item": item})


@router.put("/{item_id}")
def update_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    person_name: str = Form(""),
    title: str = Form(""),
    tag: str = Form("open"),
    deep_dive_date: str = Form(""),
    context: str = Form(""),
):
    item = db.query(ParkingItem).get(item_id)
    item.person_name = person_name
    item.title = title
    item.tag = tag
    item.deep_dive_date = deep_dive_date
    item.context = context
    db.commit()
    db.refresh(item)
    return templates.TemplateResponse("partials/parking_item.html", {**_ctx(request, db), "item": item})


@router.put("/{item_id}/toggle-closed")
def toggle_closed(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(ParkingItem).get(item_id)
    item.closed = 0 if item.closed else 1
    db.commit()
    db.refresh(item)
    return templates.TemplateResponse("partials/parking_item.html", {**_ctx(request, db), "item": item})


@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ParkingItem).get(item_id)
    if item:
        db.delete(item)
        db.commit()
    return Response(status_code=200, content="")


@router.post("")
def create_item(
    request: Request,
    db: Session = Depends(get_db),
    person_name: str = Form(""),
    title: str = Form(""),
    tag: str = Form("open"),
    deep_dive_date: str = Form(""),
    context: str = Form(""),
):
    max_order = db.query(ParkingItem).filter(ParkingItem.person_name == person_name).count()
    item = ParkingItem(
        person_name=person_name,
        title=title,
        tag=tag,
        deep_dive_date=deep_dive_date,
        context=context,
        display_order=max_order + 1,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return _render_section(request, db)


def _render_section(request, db):
    members = db.query(Member).order_by(Member.display_order).all()
    items = db.query(ParkingItem).order_by(ParkingItem.display_order).all()
    groups = _group_items_by_member_order(items, members)

    return templates.TemplateResponse("partials/parking_section.html", {
        **_ctx(request, db),
        "parking_groups": groups,
    })
