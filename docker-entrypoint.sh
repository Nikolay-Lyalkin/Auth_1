set -e

poetry run alembic upgrade head

poetry run python cli.py init-superuser

cd /app

poetry run gunicorn -w 4 -k uvicorn_worker.UvicornWorker src.main:app --bind 0.0.0.0:8001