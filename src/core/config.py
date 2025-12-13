import os

from dotenv import load_dotenv
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
    authjwt_secret_key: str = "authjwt_secret_key"
    authjwt_algorithm: str = "authjwt_algorithm"

    allowed_hosts: str = "127.0.0.1, localhost, web, 0.0.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
