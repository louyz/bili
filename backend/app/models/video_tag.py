from sqlalchemy import Column, BigInteger, String, DateTime, func
from app.models.base import Base


class VideoTag(Base):
    __tablename__ = "video_tags"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bvid = Column(String(20), nullable=False)
    tag_name = Column(String(100), nullable=False)
    crawl_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())