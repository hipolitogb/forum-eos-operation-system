from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False, default="")
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class ParkingItem(Base):
    __tablename__ = "parking_items"

    id = Column(Integer, primary_key=True)
    person_name = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    tag = Column(String(100), nullable=False, default="open")
    deep_dive_date = Column(String(50), nullable=False, default="")
    context = Column(Text, nullable=False, default="")
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
