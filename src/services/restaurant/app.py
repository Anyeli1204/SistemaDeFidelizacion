from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from application.ports import ConsumoPublisher
from application.use_cases.register_consumption import RegistrarConsumoUseCase
from common.api_schemas import (
    ErrorResponse,
    HealthResponse,
    RegistrarConsumoRequest,
    RegistrarConsumoResponse,
)
from infrastructure.rabbitmq.factory import crear_consumo_publisher

OPENAPI_TAGS = [
    {
        "name": "Consumos",
        "description": "Registro de cenas y publicación de eventos `consumo.registrado` en RabbitMQ.",
    },
    {
        "name": "Salud",
        "description": "Verificación de disponibilidad del microservicio productor.",
    },
]

app = FastAPI(
    title="API Restaurante — Programa de fidelización",
    description=(
        "Microservicio **productor** del laboratorio CS3081. "
        "Registra el consumo del cliente y publica un mensaje al broker con: "
        "monto, tarjeta, código de restaurante y fecha/hora.\n\n"
        "**Swagger UI:** `/docs` · **ReDoc:** `/redoc` · **OpenAPI JSON:** `/openapi.json`"
    ),
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    servers=[
        {"url": "http://localhost:8000", "description": "Desarrollo local"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_publisher: ConsumoPublisher | None = None


def _obtener_caso_uso() -> RegistrarConsumoUseCase:
    global _publisher
    if _publisher is None:
        _publisher = crear_consumo_publisher()
    return RegistrarConsumoUseCase(_publisher)


@app.post(
    "/api/consumos",
    status_code=202,
    tags=["Consumos"],
    summary="Registrar consumo y publicar evento",
    response_description="Consumo aceptado; mensaje enviado al broker.",
    responses={
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        503: {"model": ErrorResponse, "description": "Broker RabbitMQ no disponible"},
    },
)
def registrar_consumo(body: RegistrarConsumoRequest) -> RegistrarConsumoResponse:
    try:
        mensaje = _obtener_caso_uso().ejecutar(
            monto_consumido=body.monto_consumido,
            numero_tarjeta=body.numero_tarjeta,
            codigo_restaurante=body.codigo_restaurante,
            fecha_hora=body.fecha_hora,
            email_cliente=str(body.email_cliente) if body.email_cliente else None,
        )
        return RegistrarConsumoResponse(
            mensaje="Consumo registrado y publicado al broker",
            transaccion_id=str(mensaje.transaccion_id),
            routing_key="consumo.registrado",
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo publicar en RabbitMQ: {error}",
        ) from error


@app.get(
    "/health",
    tags=["Salud"],
    summary="Health check",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", servicio="restaurante-productor")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=OPENAPI_TAGS,
        servers=app.servers,
    )
    schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
