from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pika
import pytest

from common.constants import EXCHANGE_LOYALTY, QUEUE_REWARDS, ROUTING_CONSUMO_REGISTRADO
from common.schemas import ConsumoRegistradoMensaje
from infrastructure.rabbitmq.connection import declarar_topologia, obtener_parametros
from infrastructure.rabbitmq.publisher import RabbitMqConsumoPublisher

pytestmark = pytest.mark.integration


@pytest.mark.usefixtures("require_broker")
def test_integracion_conexion_amqp_real():
    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    canal.close()
    conexion.close()


@pytest.mark.usefixtures("require_broker")
def test_integracion_topologia_lealtad():
    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    declarar_topologia(canal)
    canal.exchange_declare(exchange=EXCHANGE_LOYALTY, passive=True)
    canal.queue_declare(queue=QUEUE_REWARDS, passive=True)
    canal.close()
    conexion.close()


@pytest.mark.usefixtures("require_broker")
def test_integracion_publicar_consumo_en_exchange():
    transaccion_id = uuid4()
    mensaje = ConsumoRegistradoMensaje(
        transaccion_id=transaccion_id,
        monto_consumido=99.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-TEST",
        fecha_hora=datetime.now(timezone.utc),
    )

    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    declarar_topologia(canal)

    cola_prueba = f"test.integracion.{uuid4().hex}"
    canal.queue_declare(queue=cola_prueba, exclusive=True, auto_delete=True)
    canal.queue_bind(
        exchange=EXCHANGE_LOYALTY,
        queue=cola_prueba,
        routing_key=ROUTING_CONSUMO_REGISTRADO,
    )

    cuerpo = mensaje.model_dump(mode="json")
    canal.basic_publish(
        exchange=EXCHANGE_LOYALTY,
        routing_key=ROUTING_CONSUMO_REGISTRADO,
        body=json.dumps(cuerpo, default=str),
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
    )

    metodo, _propiedades, recibido = canal.basic_get(queue=cola_prueba, auto_ack=True)
    canal.close()
    conexion.close()

    assert metodo is not None, "El broker no entregó el mensaje a la cola de prueba"
    datos = json.loads(recibido.decode("utf-8"))
    assert datos["transaccion_id"] == str(transaccion_id)
    assert datos["codigo_restaurante"] == "REST-TEST"


@pytest.mark.usefixtures("require_broker")
def test_integracion_publisher_del_proyecto():
    mensaje = ConsumoRegistradoMensaje(
        monto_consumido=10.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-PUB",
        fecha_hora=datetime.now(timezone.utc),
    )
    publicador = RabbitMqConsumoPublisher()
    try:
        publicador.publicar_consumo(mensaje)
    finally:
        publicador.cerrar()
