import json
from collections.abc import Callable
from typing import TypeVar

import pika
from pydantic import BaseModel

from infrastructure.rabbitmq.connection import declarar_topologia, obtener_parametros

T = TypeVar("T", bound=BaseModel)


def _crear_conexion() -> tuple[pika.BlockingConnection, pika.adapters.blocking_connection.BlockingChannel]:
    connection = pika.BlockingConnection(obtener_parametros())
    channel = connection.channel()
    declarar_topologia(channel)
    channel.basic_qos(prefetch_count=1)
    return connection, channel


def consumir_cola(
    nombre_cola: str,
    modelo: type[T],
    manejador: Callable[[T], None],
) -> None:
    connection, channel = _crear_conexion()

    def callback(ch, method, _properties, body):
        try:
            datos = json.loads(body.decode("utf-8"))
            mensaje = modelo.model_validate(datos)
            manejador(mensaje)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except ValueError as error:
            print(f"[ERROR] Mensaje inválido en {nombre_cola}: {error}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=nombre_cola, on_message_callback=callback)
    print(f"[*] Escuchando cola '{nombre_cola}'...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()
