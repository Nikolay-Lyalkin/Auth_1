# Сервис авторизации

Асинхронный микросервис авторизации на FastAPI: JWT-токены (access/refresh),
ролевая модель доступа, OAuth2-вход через Яндекс, история входов и
distributed tracing запросов.

## Возможности

- Регистрация и вход по email/логину с выдачей access и refresh JWT-токенов
- Обновление данных пользователя
- Logout с занесением токена в чёрный список в Redis до истечения срока действия — повторно использовать тот же токен после выхода нельзя
- История входов пользователя
- OAuth2-авторизация через Яндекс (redirect + callback)
- Ролевая модель доступа: декоратор `@roles_required`, создание ролей доступно только пользователям с ролью `superuser`
- Distributed tracing через OpenTelemetry + Jaeger, request correlation ID в middleware на каждый запрос

## Стек

Python 3.11 · FastAPI (async) · SQLAlchemy (async) + Alembic · PostgreSQL · Redis · async-fastapi-jwt-auth · OAuth2 (Яндекс) · OpenTelemetry / Jaeger · Docker / docker-compose · Nginx · Poetry

## Быстрый старт

Скопируйте `.env.sample` в `.env` и заполните переменные — обязательно задайте свой `AUTHJWT_SECRET_KEY` (минимум 32 символа), и, если нужен вход через Яндекс, `YANDEX_CLIENT_ID`/`YANDEX_CLIENT_SECRET`.

    docker-compose up --build

При первой инициализации автоматически создаётся пользователь с ролью `superuser`.
⚠️ Сейчас его учётные данные захардкожены в коде — перед публичным/боевым использованием стоит вынести их в переменные окружения.

API доступен на `http://localhost:8001`, документация — на `/openapi`.

## Архитектура

- **web** — FastAPI-приложение, асинхронная обработка запросов
- **db** — PostgreSQL, миграции через Alembic
- **redis** — кэш и чёрный список отозванных токенов
- **nginx** — обратный прокси

## Что дальше

- [ ] Вынести дефолтные креды superuser из кода в переменные окружения
- [ ] Покрыть тестами (сейчас автотестов нет — ближайший приоритет)
- [ ] Добавить CI/CD по аналогии с `Atomic_Habits` (lint + test)
