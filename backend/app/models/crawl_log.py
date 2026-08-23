from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text, Enum, func
from app.models.base import Base


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)
    status = Column(Enum("pending", "running", "success", "failed", "partial"), nullable=False, default="pending")
    trigger_type = Column(Enum("scheduled", "manual"), nullable=False, default="scheduled")
    total_videos = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    error_msg = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class CrawlLogDetail(Base):
    __tablename__ = "crawl_log_details"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    log_id = Column(BigInteger, nullable=False)
    bvid = Column(String(20), nullable=False)
    api_step = Column(Integer, nullable=False)
    api_url = Column(String(500), nullable=True)
    status = Column(Enum("success", "failed", "skipped"), nullable=False)
    http_status = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    error_msg = Column(String(1000), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())