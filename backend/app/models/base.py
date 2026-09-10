from app.database import engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def create_tables():
    """非异步建表函数，仅供初始化使用"""
    import asyncio
    from sqlalchemy import text

    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())