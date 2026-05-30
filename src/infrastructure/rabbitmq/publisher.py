import json
import threading

import pika
from pika import exceptions as pika_exceptions

from application.ports import ConsumoPublisher, RecompensaPublisher
from common.constants import (
    EXCHANGE_LOYALTY,
    ROUTING_CONSUMO_REGISTRADO,
    ROUTING_RECOMPENSA_PROCESADA,
)
from common.schemas import ConsumoRegistradoMensaje, RecompensaProcesadaMensaje
from infrastructure.rabbitmq.connection import declarar_topologia, obtener_parametros


class RabbitMqConsumoPublisher(ConsumoPublisher):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._connect()

    def _connect(self) -> None:
        self._connection = pika.BlockingConnection(obtener_parametros())
        self._channel = self._connection.channel()
        declarar_topologia(self._channel)

    def _ensure_connection(self) -> None:
        if (
            self._connection is None
            or self._channel is None
            or self._connection.is_closed
            or self._channel.is_closed
        ):
            self._connect()

    def publicar_consumo(self, mensaje: ConsumoRegistradoMensaje) -> None:
        cuerpo = mensaje.model_dump(mode="json")
        with self._lock:
            for intento in (1, 2):
                try:
                    self._ensure_connection()
                    assert self._channel is not None
                    self._channel.basic_publish(
                        exchange=EXCHANGE_LOYALTY,
                        routing_key=ROUTING_CONSUMO_REGISTRADO,
                        body=json.dumps(cuerpo, default=str),
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            content_type="application/json",
                        ),
                    )
                    return
                except (
                    pika_exceptions.AMQPConnectionError,
                    pika_exceptions.StreamLostError,
                    pika_exceptions.ChannelWrongStateError,
                ):
                    self.cerrar()
                    if intento == 2:
                        raise

    def cerrar(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
        self._connection = None
        self._channel = None


class RabbitMqRecompensaPublisher(RecompensaPublisher):
    def __init__(self, channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
        self._channel = channel

    def publicar_recompensa(self, mensaje: RecompensaProcesadaMensaje) -> None:
        cuerpo = mensaje.model_dump(mode="json")
        self._channel.basic_publish(
            exchange=EXCHANGE_LOYALTY,
            routing_key=ROUTING_RECOMPENSA_PROCESADA,
            body=json.dumps(cuerpo, default=str),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
