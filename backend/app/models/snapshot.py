from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Date, Float, func
from app.models.base import Base


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bvid = Column(String(20), nullable=False)
    video_id = Column(BigInteger, nullable=False)
    up_id = Column(BigInteger, nullable=False)
    play_count = Column(BigInteger, nullable=False, default=0)
    danmaku_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    like_count = Column(Integer, nullable=False, default=0)
    coin_count = Column(Integer, nullable=False, default=0)
    favorite_count = Column(Integer, nullable=False, default=0)
    share_count = Column(Integer, nullable=False, default=0)
    play_increment = Column(BigInteger, nullable=True)
    danmaku_increment = Column(Integer, nullable=True)
    comment_increment = Column(Integer, nullable=True)
    like_increment = Column(Integer, nullable=True)
    coin_increment = Column(Integer, nullable=True)
    favorite_increment = Column(Integer, nullable=True)
    share_increment = Column(Integer, nullable=True)
    interaction_rate = Column(Float, nullable=True)
    heat_score = Column(Float, nullable=True)
    rank_position = Column(Integer, nullable=True)
    snapshot_date = Column(Date, nullable=False)
    snapshot_hour = Column(Integer, nullable=True)
    crawl_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class UpUserSnapshot(Base):
    __tablename__ = "up_user_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    up_id = Column(BigInteger, nullable=False)
    up_uid = Column(BigInteger, nullable=False)
    follower_count = Column(BigInteger, nullable=False, default=0)
    following_count = Column(BigInteger, nullable=False, default=0)
    total_likes = Column(BigInteger, nullable=False, default=0)
    total_plays = Column(BigInteger, nullable=False, default=0)
    video_count = Column(Integer, nullable=False, default=0)
    follower_increment = Column(Integer, nullable=True)
    total_likes_increment = Column(BigInteger, nullable=True)
    total_plays_increment = Column(BigInteger, nullable=True)
    snapshot_date = Column(Date, nullable=False)
    crawl_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())