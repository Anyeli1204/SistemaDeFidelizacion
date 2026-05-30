from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pika
import pytest

from application.use_cases.notify_reward import NotificarRecompensaUseCase
from common.constants import (
    EXCHANGE_LOYALTY,
    QUEUE_NOTIFICATIONS,
    ROUTING_RECOMPENSA_PROCESADA,
)
from common.schemas import RecompensaProcesadaMensaje
from infrastructure.notifications.email_notifier import EmailNotificador
from infrastructure.rabbitmq.connection import declarar_topologia, obtener_parametros
from infrastructure.rabbitmq.publisher import RabbitMqRecompensaPublisher

pytestmark = pytest.mark.integration


def _mensaje_recompensa(email: str = "integracion@test.lab") -> RecompensaProcesadaMensaje:
    return RecompensaProcesadaMensaje(
        transaccion_id=uuid4(),
        numero_tarjeta="4111111111111111",
        puntos_abonados=7,
        saldo_total=17,
        codigo_restaurante="REST-NOTIF",
        procesado_en=datetime.now(timezone.utc),
        email_cliente=email,
        enviar_notificacion_email=True,
    )


def _cola_temporal_recompensa(canal: pika.adapters.blocking_connection.BlockingChannel) -> str:
    nombre = f"test.notif.{uuid4().hex}"
    canal.queue_declare(queue=nombre, exclusive=True, auto_delete=True)
    canal.queue_bind(
        exchange=EXCHANGE_LOYALTY,
        queue=nombre,
        routing_key=ROUTING_RECOMPENSA_PROCESADA,
    )
    return nombre


@pytest.mark.usefixtures("require_broker")
def test_integracion_cola_notificaciones_en_broker():
    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    declarar_topologia(canal)
    canal.queue_declare(queue=QUEUE_NOTIFICATIONS, passive=True)
    canal.close()
    conexion.close()


@pytest.mark.usefixtures("require_broker")
def test_integracion_publicar_recompensa_en_exchange():
    mensaje = _mensaje_recompensa()
    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    declarar_topologia(canal)
    cola = _cola_temporal_recompensa(canal)

    RabbitMqRecompensaPublisher(canal).publicar_recompensa(mensaje)
    metodo, _props, cuerpo = canal.basic_get(queue=cola, auto_ack=True)
    canal.close()
    conexion.close()

    assert metodo is not None
    datos = json.loads(cuerpo.decode("utf-8"))
    assert datos["email_cliente"] == "integracion@test.lab"
    assert datos["puntos_abonados"] == 7


@pytest.mark.usefixtures("require_broker")
def test_integracion_notificar_recompensa_tras_evento_rabbit(tmp_path):
    log = tmp_path / "notif_integracion.log"
    mensaje = _mensaje_recompensa("cliente.integracion@test.lab")

    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    declarar_topologia(canal)
    cola = _cola_temporal_recompensa(canal)
    RabbitMqRecompensaPublisher(canal).publicar_recompensa(mensaje)
    _metodo, _props, cuerpo = canal.basic_get(queue=cola, auto_ack=True)
    canal.close()
    conexion.close()

    evento = RecompensaProcesadaMensaje.model_validate(json.loads(cuerpo.decode("utf-8")))
    NotificarRecompensaUseCase(EmailNotificador(log_path=log)).ejecutar(evento)

    texto = log.read_text(encoding="utf-8")
    assert "cliente.integracion@test.lab" in texto
    assert "Se abonaron 7 puntos" in texto


@pytest.mark.usefixtures("require_broker")
def test_integracion_worker_notificacion_mismo_flujo_que_produccion(tmp_path, capsys):
    from services.notification import worker

    log = tmp_path / "worker_integracion.log"
    mensaje = _mensaje_recompensa("worker.integracion@test.lab")

    conexion = pika.BlockingConnection(obtener_parametros())
    canal = conexion.channel()
    declarar_topologia(canal)
    cola = _cola_temporal_recompensa(canal)
    RabbitMqRecompensaPublisher(canal).publicar_recompensa(mensaje)
    _metodo, _props, cuerpo = canal.basic_get(queue=cola, auto_ack=True)
    canal.close()
    conexion.close()

    evento = RecompensaProcesadaMensaje.model_validate(json.loads(cuerpo.decode("utf-8")))
    notificador = EmailNotificador(log_path=log)
    caso = NotificarRecompensaUseCase(notificador)

    def manejar(msg: RecompensaProcesadaMensaje) -> None:
        caso.ejecutar(msg)

    manejar(evento)

    assert "worker.integracion@test.lab" in log.read_text(encoding="utf-8")
    assert worker.QUEUE_NOTIFICATIONS == "notifications.recompensa"
