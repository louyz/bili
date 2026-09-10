from sqlalchemy import Column, BigInteger, String, Integer, Enum, DateTime, func
from app.models.base import Base


class UpUser(Base):
    __tablename__ = "up_users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="UP主记录主键ID")
    up_uid = Column(BigInteger, nullable=False, unique=True, comment="B站UP主UID")
    nickname = Column(String(100), nullable=False, comment="UP主昵称")
    sex = Column(Enum("男", "女", "保密"), default="保密", comment="性别")
    level = Column(Integer, default=0, comment="等级 Lv0-Lv6")
    sign = Column(String(500), nullable=True, comment="个人签名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    official_role = Column(Integer, default=0, comment="认证类型: 0=无,1=个人,2=机构,3=媒体,4=政府,5=电视,6=明星,7=虚拟主播")
    official_title = Column(String(200), nullable=True, comment="认证称号")
    follower_count = Column(BigInteger, nullable=False, default=0, comment="粉丝数")
    following_count = Column(BigInteger, nullable=False, default=0, comment="关注数")
    total_likes = Column(BigInteger, nullable=False, default=0, comment="总获赞数")
    total_plays = Column(BigInteger, nullable=False, default=0, comment="总播放量")
    video_count = Column(Integer, nullable=False, default=0, comment="视频数")
    elec = Column(Integer, nullable=False, default=0, comment="充电数")
    audio_count = Column(Integer, nullable=False, default=0, comment="音频数")
    image_text_count = Column(Integer, nullable=False, default=0, comment="图文数")
    total = Column(Integer, nullable=False, default=0, comment="总作品数")
    crawl_time = Column(DateTime, nullable=False, comment="采集时间")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="首次录入时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="最近更新时间")