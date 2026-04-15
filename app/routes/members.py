from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Member

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _member_names(db: Session) -> list[str]:
    names = [m.name for m in db.query(Member).order_by(Member.display_order).all()]
    return names + ["Group"]


@router.post("")
def create_member(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(""),
    role: str = Form(""),
):
    max_order = db.query(Member).count()
    member = Member(name=name, role=role, display_order=max_order + 1)
    db.add(member)
    db.commit()
    db.refresh(member)
    # Return the chip plus an out-of-band swap of the parking add-form select,
    # so adding a member immediately updates the person picker in the Parking
    # Lot tab without needing a full page reload.
    chip_html = templates.get_template("partials/member_chip.html").render(
        request=request, member=member,
    )
    select_html = templates.get_template("partials/parking_person_select.html").render(
        request=request, member_names=_member_names(db),
    )
    return Response(content=chip_html + select_html, media_type="text/html")


@router.delete("/{member_id}")
def delete_member(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = db.query(Member).get(member_id)
    if member:
        db.delete(member)
        db.commit()
    # Empty string replaces the chip (hx-target removes it); the OOB select
    # fragment refreshes the Parking Lot person picker.
    select_html = templates.get_template("partials/parking_person_select.html").render(
        request=request, member_names=_member_names(db),
    )
    return Response(content=select_html, media_type="text/html")
