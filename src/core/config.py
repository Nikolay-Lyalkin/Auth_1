from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project
    projrct_name: str = "auth_users"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379

    # PostgreSQL
    postgres_db: str = "auth_database"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    database_host: str = "db"
    database_port: int = 5432

    # AuthJwt
    authjwt_secret_key: str = "your-super-secret-key-minimum-32-chars"
    authjwt_algorithm: str = "HS256"

    allowed_hosts: str = "127.0.0.1, localhost, web, 0.0.0.0"

    yandex_client_id: str
    yandex_redirect_uri: str = "http://localhost:8001/auth/yandex/callback"
    yandex_client_secret: str

    @property
    def yandex_redirect_url(self) -> str:
        return f"https://oauth.yandex.ru/authorize?response_type=code&client_id={self.yandex_client_id}&redirect_uri={self.yandex_redirect_uri}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
