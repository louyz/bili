from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UpUserInfo(BaseModel):
    id: int
    up_uid: int
    nickname: str
    sex: Optional[str] = None
    level: int
    sign: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: int
    following_count: int
    total_likes: int
    total_plays: int
    video_count: int

    class Config:
        from_attributes = True


class VideoListItem(BaseModel):
    id: int
    bvid: str
    title: str
    cover_url: Optional[str] = None
    play_count: int
    danmaku_count: int
    comment_count: int
    like_count: int
    coin_count: int
    favorite_count: int
    share_count: int
    duration: int
    pub_time: datetime
    partition_main: str
    partition_sub: Optional[str] = None
    interaction_rate: Optional[float] = None
    heat_score: Optional[float] = None
    up_nickname: Optional[str] = None
    up_follower_count: Optional[int] = None
    tags: Optional[List[str]] = None
    crawl_time: datetime

    class Config:
        from_attributes = True


class VideoDetail(BaseModel):
    id: int
    bvid: str
    title: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    play_count: int
    danmaku_count: int
    comment_count: int
    like_count: int
    coin_count: int
    favorite_count: int
    share_count: int
    duration: int
    pub_time: datetime
    partition_main: str
    partition_sub: Optional[str] = None
    interaction_rate: Optional[float] = None
    heat_score: Optional[float] = None
    up_user: Optional[UpUserInfo] = None
    tags: Optional[List[str]] = None
    crawl_time: datetime

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[VideoListItem]


class DashboardStats(BaseModel):
    total_videos: int
    today_new_videos: int
    avg_play_count: float
    active_up_count: int


class TrendDataPoint(BaseModel):
    date: str
    avg_play_count: float
    video_count: int


class PartitionStat(BaseModel):
    partition: str
    count: int
    avg_heat_score: float


class TagFrequencyItem(BaseModel):
    tag_name: str
    video_count: int
    avg_play_count: float
    avg_heat_score: float