from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Boolean, Text, Float, func
from app.models.base import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bvid = Column(String(20), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    cover_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    play_count = Column(BigInteger, nullable=False, default=0)
    danmaku_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    like_count = Column(Integer, nullable=False, default=0)
    coin_count = Column(Integer, nullable=False, default=0)
    favorite_count = Column(Integer, nullable=False, default=0)
    share_count = Column(Integer, nullable=False, default=0)
    duration = Column(Integer, nullable=False, default=0)
    pub_time = Column(DateTime, nullable=False)
    partition_main = Column(String(50), nullable=False, default="未知")
    partition_sub = Column(String(50), nullable=True)
    up_id = Column(BigInteger, nullable=False)
    up_uid = Column(BigInteger, nullable=False)
    interaction_rate = Column(Float, nullable=True)
    heat_score = Column(Float, nullable=True)
    crawl_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())