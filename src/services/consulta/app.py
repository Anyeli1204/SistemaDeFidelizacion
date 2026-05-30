from typing import Annotated

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from application.ports import CuentaRecompensasRepository
from application.use_cases.consult_balance import ConsultarSaldoUseCase
from common.api_schemas import ErrorResponse, HealthResponse, SaldoResponse
from domain.rewards import CuentaNoEncontradaError
from infrastructure.persistence.factory import crear_repositorio_cuentas

OPENAPI_TAGS = [
    {
        "name": "Cuentas",
        "description": "Consulta del saldo de puntos tras procesar eventos de consumo.",
    },
    {
        "name": "Salud",
        "description": "Verificación de disponibilidad del servicio de consulta.",
    },
]

app = FastAPI(
    title="API Consulta de puntos — Programa de fidelización",
    description=(
        "Microservicio de **consulta** del saldo de recompensas (lectura en SQLite). "
        "Los puntos se acumulan cuando el worker de recompensas procesa mensajes de RabbitMQ.\n\n"
        "**Swagger UI:** `/docs` · **ReDoc:** `/redoc`"
    ),
    version="1.0.0",
    openapi_tags=OPENAPI_TAGS,
    servers=[
        {"url": "http://localhost:8001", "description": "Desarrollo local"},
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

_repositorio: CuentaRecompensasRepository = crear_repositorio_cuentas()


def _obtener_caso_uso() -> ConsultarSaldoUseCase:
    return ConsultarSaldoUseCase(_repositorio)


@app.get(
    "/api/cuentas/{numero_tarjeta}/saldo",
    tags=["Cuentas"],
    summary="Consultar saldo de puntos",
    responses={
        404: {"model": ErrorResponse, "description": "No existe cuenta para esa tarjeta"},
    },
)
def obtener_saldo(
    numero_tarjeta: Annotated[
        str,
        Path(
            description="Número de tarjeta del cliente (se normalizan espacios y guiones).",
            examples=["4111111111111111"],
        ),
    ],
) -> SaldoResponse:
    try:
        resultado = _obtener_caso_uso().ejecutar(numero_tarjeta)
    except CuentaNoEncontradaError:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada") from None
    return SaldoResponse(
        numero_tarjeta=resultado.numero_tarjeta,
        saldo_puntos=resultado.saldo_puntos,
    )


@app.get(
    "/health",
    tags=["Salud"],
    summary="Health check",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", servicio="consulta-puntos")


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
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
