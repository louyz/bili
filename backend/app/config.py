from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "B站热门视频数据分析平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root123456"
    DB_NAME: str = "mydb"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    JWT_SECRET_KEY: str = "bili-hot-analysis-jwt-secret-key-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    CRAWL_INTERVAL_SECONDS: int = 7200
    CRAWL_MAX_RETRY: int = 3
    CRAWL_REQUEST_DELAY: float = 2.0
    CRAWL_POPULAR_PAGES: int = 2

    CRAWL_DELAY_MIN: float = 5.0
    CRAWL_DELAY_MAX: float = 15.0
    CRAWL_RATE_LIMIT_BACKOFF: float = 60.0

    # B站 API 凭证 (bilibili-api-python Credential)
    BILI_SESSDATA: str = "2d72304d%2C1804558011%2C53054%2A91CjC3si92ikC0KfZbk1dYi-dQ5rzFGss7788hOU3yd7UxRRerRy7J4MfsceAikxBqLDISVnpIZGpscjgzalBNMjZVNDNna3B3Wlo0QU04SktrUFlsWjhNVUZNUzBtNFVNaXVZUWJRck41SjRkS1BhcVlRUEc5ZkpVNXVvcDBnalpvcUQ5aGxYMXhRIIEC"
    BILI_BUVID3: str = "B99B0FC9-6BAF-88AB-1A76-9FA1EAFEB82185644infoc"
    BILI_BILI_JCT: str = "2a30342f0da68782cc17f321528fcccf"
    BILI_DEDEUSERID: str = "524773339"
    BILI_BUVID4: str = "E9432806-D457-27F2-8D18-5A32B4AEC90F86086-026090709-Xaurtx2L65LHdhERWBiJ0g%3D%3D"
    BILI_BUVID_FP: str = "976b907750393c6309c01ff28478aefc"
    BILI_B_NUT: str = "1788744185"
    BILI_UUID: str = "10ABFEE1F-7D93-1397-36F3-5ECA75BDC72787410infoc"
    BILI_BILI_TICKET: str = "eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3ODkyMjQ5ODIsImlhdCI6MTc4ODk2NTcyMiwicGx0IjotMX0.NndbX4D0Igsk_123jpTiEym5-VbKPyswfN0YwOAeWns"
    BILI_BILI_TICKET_EXPIRES: str = "1789224922"
    BILI_SID: str = "8gzjtrcf"
    BILI_B_LSID: str = "8AA22254_1A0896ADE03"

    # 兼容旧版: 完整 Cookie 字符串 (如果设置了结构化凭证则优先使用结构化凭证)
    CRAWL_BILI_COOKIE: str = ""

    def get_bili_credential_kwargs(self) -> dict:
        if self.BILI_SESSDATA:
            return {
                "sessdata": self.BILI_SESSDATA,
                "buvid3": self.BILI_BUVID3,
                "bili_jct": self.BILI_BILI_JCT,
                "dedeuserid": self.BILI_DEDEUSERID,
                "buvid4": self.BILI_BUVID4,
            }
        if self.CRAWL_BILI_COOKIE:
            return {"cookie": self.CRAWL_BILI_COOKIE}
        return {}

    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()