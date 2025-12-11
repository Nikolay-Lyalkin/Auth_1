import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):

    # Project
    PROJECT_NAME: str = "auth_users"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # PostgreSQL
    POSTGRES_DB: str = "auth_database"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    DATABASE_HOST: str = "db"
    DATABASE_PORT: int = 5432

    # AuthJwt
    authjwt_secret_key: str = os.getenv("AUTHJWT_SECRET_KEY")
    authjwt_algorithm: str = os.getenv("AUTHJWT_ALGORITHM")


settings = Settings()
