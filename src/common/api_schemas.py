from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegistrarConsumoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "monto_consumido": 120.0,
                    "numero_tarjeta": "4111111111111111",
                    "codigo_restaurante": "REST-LIMA-01",
                    "fecha_hora": "2026-05-27T20:00:00Z",
                    "email_cliente": "cliente@ejemplo.com",
                }
            ]
        }
    )

    monto_consumido: float = Field(
        ...,
        gt=0,
        description="Monto total consumido en la cena (moneda local).",
        examples=[120.5],
    )
    numero_tarjeta: str = Field(
        ...,
        description="Número de tarjeta del cliente en el programa de fidelización.",
        examples=["4111111111111111"],
    )
    codigo_restaurante: str = Field(
        ...,
        description="Código del restaurante afiliado que registró el consumo.",
        examples=["REST-LIMA-01"],
    )
    fecha_hora: datetime | None = Field(
        default=None,
        description="Fecha y hora de la transacción (UTC). Si se omite, se usa la hora actual.",
    )
    email_cliente: EmailStr | None = Field(
        default=None,
        description=(
            "Correo del cliente. Se guarda en la cuenta solo la primera vez; "
            "la notificación por email se envía solo en ese primer registro."
        ),
    )


class RegistrarConsumoResponse(BaseModel):
    mensaje: str = Field(
        examples=["Consumo registrado y publicado al broker"],
    )
    transaccion_id: str = Field(
        description="Identificador único de la transacción (idempotencia).",
        examples=["a11e8b11-949b-44b3-9c53-b9259b8db81d"],
    )
    routing_key: str = Field(
        description="Clave de enrutamiento en RabbitMQ.",
        examples=["consumo.registrado"],
    )


class SaldoResponse(BaseModel):
    numero_tarjeta: str = Field(examples=["4111111111111111"])
    saldo_puntos: int = Field(
        description="Puntos acumulados en la cuenta de recompensas.",
        examples=[12],
    )


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    servicio: str = Field(examples=["restaurante-productor"])


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["Cuenta no encontrada"])
