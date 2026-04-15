from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Member

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
    return templates.TemplateResponse("partials/member_chip.html", {"request": request, "member": member})


@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).get(member_id)
    if member:
        db.delete(member)
        db.commit()
    return Response(status_code=200, content="")
