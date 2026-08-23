from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "B站热门视频数据分析平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DB_HOST: str = "118.190.78.149"
    DB_PORT: int = 3306
    DB_USER: str = "bili_hot"
    DB_PASSWORD: str = "rWW3WZTLYDM5886M"
    DB_NAME: str = "bili_hot"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    JWT_SECRET_KEY: str = "bili-hot-analysis-jwt-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    CRAWL_INTERVAL_SECONDS: int = 7200
    CRAWL_MAX_RETRY: int = 3
    CRAWL_REQUEST_DELAY: float = 2.0
    CRAWL_POPULAR_PAGES: int = 2

    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()