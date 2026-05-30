
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


class ConsumoInvalidoError(ValueError):
    pass


@dataclass(frozen=True)
class Consumo:
    transaccion_id: UUID
    monto_consumido: float
    numero_tarjeta: str
    codigo_restaurante: str
    fecha_hora: datetime


def validar_consumo(consumo: Consumo) -> Consumo:
    if consumo.monto_consumido <= 0:
        raise ConsumoInvalidoError("monto_consumido debe ser positivo")
    if not consumo.numero_tarjeta:
        raise ConsumoInvalidoError("numero_tarjeta es obligatorio")
    if not consumo.codigo_restaurante:
        raise ConsumoInvalidoError("codigo_restaurante es obligatorio")
    return consumo
