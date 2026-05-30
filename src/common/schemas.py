
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator


class ConsumoRegistradoMensaje(BaseModel):
    transaccion_id: UUID = Field(default_factory=uuid4)
    monto_consumido: float = Field(gt=0)
    numero_tarjeta: str = Field(min_length=8, max_length=19)
    codigo_restaurante: str = Field(min_length=1, max_length=20)
    fecha_hora: datetime
    email_cliente: EmailStr | None = Field(
        default=None,
        description="Correo del cliente; se persiste solo la primera vez en la cuenta.",
    )

    @field_validator("numero_tarjeta")
    @classmethod
    def tarjeta_sin_espacios(cls, valor: str) -> str:
        limpio = valor.replace(" ", "").replace("-", "")
        if not limpio.isdigit():
            raise ValueError("numero_tarjeta debe contener solo dígitos")
        return limpio

    @field_validator("codigo_restaurante")
    @classmethod
    def codigo_mayusculas(cls, valor: str) -> str:
        return valor.strip().upper()


class RecompensaProcesadaMensaje(BaseModel):
    transaccion_id: UUID
    numero_tarjeta: str
    puntos_abonados: int
    saldo_total: int
    codigo_restaurante: str
    procesado_en: datetime
    email_cliente: str | None = None
    enviar_notificacion_email: bool = False
