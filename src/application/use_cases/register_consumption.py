from datetime import datetime, timezone
from uuid import uuid4

from application.ports import ConsumoPublisher
from common.schemas import ConsumoRegistradoMensaje
from domain.consumption import Consumo, validar_consumo


class RegistrarConsumoUseCase:
    def __init__(self, publisher: ConsumoPublisher) -> None:
        self._publisher = publisher

    def ejecutar(
        self,
        monto_consumido: float,
        numero_tarjeta: str,
        codigo_restaurante: str,
        fecha_hora: datetime | None = None,
        email_cliente: str | None = None,
    ) -> ConsumoRegistradoMensaje:
        transaccion_id = uuid4()
        cuando = fecha_hora or datetime.now(timezone.utc)

        consumo = validar_consumo(
            Consumo(
                transaccion_id=transaccion_id,
                monto_consumido=monto_consumido,
                numero_tarjeta=numero_tarjeta.replace(" ", "").replace("-", ""),
                codigo_restaurante=codigo_restaurante.strip().upper(),
                fecha_hora=cuando,
            )
        )

        mensaje = ConsumoRegistradoMensaje(
            transaccion_id=consumo.transaccion_id,
            monto_consumido=consumo.monto_consumido,
            numero_tarjeta=consumo.numero_tarjeta,
            codigo_restaurante=consumo.codigo_restaurante,
            fecha_hora=consumo.fecha_hora,
            email_cliente=email_cliente.strip().lower() if email_cliente else None,
        )
        self._publisher.publicar_consumo(mensaje)
        return mensaje
