import uuid
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import UUID, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import declarative_base, relationship

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Создаём базовый класс для будущих моделей
Base = declarative_base()


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь один-ко-многим: одна роль → много пользователей
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"Role {self.name}"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    login = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    login_histories = relationship("LoginHistory", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, login: str, password: str, first_name: str, last_name: str, role_id: UUID) -> None:
        self.login = login
        self.password = pwd_context.hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role_id = role_id

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password)

    def set_password(self, password: str) -> None:
        self.password = pwd_context.hash(password)

    def __repr__(self) -> str:
        return f"<User {self.login}>"


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(512))
    device_type = Column(String(50))
    login_status = Column(String(20), default="success", nullable=False)

    # Связь с пользователем
    user = relationship("User", back_populates="login_histories")

    def __init__(
        self,
        user_id: uuid.UUID,
        ip_address: str,
        user_agent: str = None,
        device_type: str = None,
        login_status: str = "success",
    ) -> None:
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.device_type = device_type
        self.login_status = login_status

    def __repr__(self) -> str:
        return f"LoginHistory {self.login_time} - {self.login_status}"
