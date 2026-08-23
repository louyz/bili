from sqlalchemy import Column, BigInteger, String, Enum, DateTime, Boolean, func
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户主键ID")
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    email = Column(String(100), nullable=False, unique=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    nickname = Column(String(50), nullable=True, comment="昵称")
    role = Column(Enum("user", "admin"), nullable=False, default="user", comment="角色")
    is_active = Column(Boolean, nullable=False, default=True, comment="启用状态")
    email_verified = Column(Boolean, nullable=False, default=False, comment="邮箱验证")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")