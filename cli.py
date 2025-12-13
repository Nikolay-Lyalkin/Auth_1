import typer

from src.db.postgres import get_session_for_cli
from src.models.user import Role, User


app = typer.Typer()


def create_role_superuser():
    """Создать роль суперпользователя"""
    with get_session_for_cli() as db:
        # Проверяем существование роли
        existing_role = db.query(Role).filter(Role.name == "superuser").first()

        if existing_role:
            return

        # Создаем новую роль
        role = Role(
            name="superuser",
            description="Суперпользователь с полными правами"
        )
        db.add(role)
        db.commit()
        return role


def create_superuser():
    with get_session_for_cli() as db:
        # Проверяем существование роли
        role = db.query(Role).filter(Role.name == "superuser").first()

        superuser = User(
            first_name="superuser",
            last_name="superuser",
            login="superuser",
            password="superuser",
            role_id=role.id,
        )

        db.add(superuser)
        db.commit()


def init_superuser_data():
    """Создать и роль и пользователя superuser"""
    role = create_role_superuser()
    if role:
        create_superuser()


@app.command()
def init_superuser():
    """Создать суперпользователя и его роль"""
    init_superuser_data()


@app.command()
def version():
    """Показать версию приложения"""
    print("1.0.0")


if __name__ == "__main__":
    app()