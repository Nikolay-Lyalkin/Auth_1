import uuid
from contextlib import asynccontextmanager

from async_fastapi_jwt_auth import AuthJWT
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes
from redis.asyncio import Redis
from fastapi import Request

from src.core.config import settings
from src.db import redis_db
from src.handlers.user_roles import router as user_role_router
from src.handlers.users import router as user_router


@AuthJWT.load_config
def get_config():
    return settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_db.redis = Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)
    yield
    # Shutdown


def configure_tracer() -> None:
    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: "auth-service",
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
        )
    )
    # Чтобы видеть трейсы в консоли
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(tracer_provider)


configure_tracer()


# Сначала создаем app
app = FastAPI(
    title=settings.projrct_name,
    docs_url="/openapi",
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def before_request(request: Request, call_next):
    # Получаем или создаем request_id
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    # Добавляем в состояние запроса
    request.state.request_id = request_id

    # Обрабатываем запрос
    response = await call_next(request)

    # Добавляем в заголовки ответа
    response.headers["X-Request-Id"] = request_id

    return response


app.include_router(user_router, prefix="", tags=["user"])
app.include_router(user_role_router, prefix="", tags=["user_role"])
