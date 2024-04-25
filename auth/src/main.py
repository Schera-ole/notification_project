from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor,
                                            ConsoleSpanExporter)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from api.v1 import manage_roles, oauth, roles, user
from core.settings import settings
from db import psql, redis
from services.rate_limit import RateLimit


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = redis.RedisRepository(Redis(host=settings.redis_host, port=settings.redis_port))
    engine = create_async_engine(str(settings.psql_dsn), echo=True, future=True)
    psql.async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield
    await redis.redis.client.close()
    await psql.async_session.close()
    await engine.dispose()


def configure_tracer() -> None:
    trace.set_tracer_provider(TracerProvider(
        resource=Resource.create({SERVICE_NAME: settings.service_jaeger_name})
    ))
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            JaegerExporter(
                agent_host_name=settings.jaeger_exporter_host,
                agent_port=settings.jaeger_exporter_port,
            )
        )
    )
    # Чтобы видеть трейсы в консоли
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))


if settings.is_enable_tracer:
    configure_tracer()

app = FastAPI(
    title='Praktikum',
    docs_url='/auth/openapi',
    openapi_url='/auth/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)


@app.middleware('http')
async def before_request(request: Request, call_next):
    response = await call_next(request)
    request_id = request.headers.get('X-Request-Id')
    if not request_id and ('openapi' not in str(request.url) and 'yandex' not in str(request.url)):
        return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'detail': 'X-Request-Id is required'})
    return response

app.include_router(user.router, prefix='/auth/v1/user', tags=['user'])
app.include_router(roles.router, prefix='/auth/v1/roles', tags=['roles'])
app.include_router(manage_roles.router, prefix='/auth/v1/manage_roles', tags=['manage roles'])
app.include_router(oauth.router, prefix='/auth/v1/oauth', tags=['oauth login'])


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=80,
    )
