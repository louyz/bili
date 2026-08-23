from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Boolean, func
from app.models.base import Base


class FavoriteFolder(Base):
    __tablename__ = "favorite_folders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    video_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    video_id = Column(BigInteger, nullable=False)
    folder_id = Column(BigInteger, nullable=True)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())