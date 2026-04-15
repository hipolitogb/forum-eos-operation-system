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


class ForumSettings(Base):
    __tablename__ = "forum_settings"

    # Singleton row: always id=1.
    id = Column(Integer, primary_key=True, default=1)
    forum_name = Column(String(100), nullable=False, default="FORUM OS")
    tagline = Column(String(200), nullable=False, default="Operations Dashboard")
    display_font = Column(String(100), nullable=False, default="Alfa Slab One")
    body_font = Column(String(100), nullable=False, default="Manrope")
    color_primary = Column(String(7), nullable=False, default="#F59E0B")
    color_secondary = Column(String(7), nullable=False, default="#EF4444")
    color_tertiary = Column(String(7), nullable=False, default="#3B82F6")
    logo_path = Column(String(300), nullable=False, default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
