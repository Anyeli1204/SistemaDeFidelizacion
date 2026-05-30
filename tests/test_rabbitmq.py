import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pika import exceptions as pika_exceptions
from common.schemas import ConsumoRegistradoMensaje, RecompensaProcesadaMensaje
from infrastructure.rabbitmq import connection, consumer, publisher


def test_cargar_dotenv_carga_variables(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "export RABBITMQ_HOST=broker.test\n"
        "RABBITMQ_PORT=5673\n"
        "RABBITMQ_USER=alumno\n"
        "RABBITMQ_PASSWORD=secreto\n",
        encoding="utf-8",
    )

    class FakePath:
        def __init__(self, *_args, **_kwargs):
            self._env = env

        def resolve(self):
            return self

        @property
        def parents(self):
            class Parents:
                def __getitem__(self, idx):
                    return tmp_path

            return Parents()

        def __truediv__(self, name):
            return self._env if name == ".env" else tmp_path / str(name)

        def is_file(self):
            return self._env.exists()

        def read_text(self, encoding="utf-8"):
            return self._env.read_text(encoding=encoding)

    monkeypatch.setattr(connection, "Path", FakePath)
    monkeypatch.delenv("RABBITMQ_HOST", raising=False)
    connection.cargar_dotenv()
    import os

    assert os.environ["RABBITMQ_HOST"] == "broker.test"


def test_cargar_dotenv_sin_archivo(monkeypatch, tmp_path):
    class FakePath:
        def __init__(self, *_args, **_kwargs):
            self._env = tmp_path / "no.env"

        def resolve(self):
            return self

        @property
        def parents(self):
            class Parents:
                def __getitem__(self, idx):
                    return tmp_path

            return Parents()

        def __truediv__(self, name):
            return self._env if name == ".env" else tmp_path / str(name)

        def is_file(self):
            return False

    monkeypatch.setattr(connection, "Path", FakePath)
    connection.cargar_dotenv()


def test_obtener_parametros_desde_entorno(monkeypatch):
    monkeypatch.setenv("RABBITMQ_HOST", "broker.test")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("RABBITMQ_PASSWORD", "secreto")
    monkeypatch.setattr(connection, "cargar_dotenv", lambda: None)
    params = connection.obtener_parametros()
    assert params.host == "broker.test"
    assert params.port == 5673


def test_declarar_topologia():
    canal = MagicMock()
    connection.declarar_topologia(canal)
    assert canal.exchange_declare.called
    assert canal.queue_declare.call_count == 2


@patch("infrastructure.rabbitmq.publisher.pika.BlockingConnection")
def test_publicar_consumo(mock_conn_cls):
    conexion = MagicMock()
    conexion.is_closed = False
    conexion.is_open = True
    canal = MagicMock()
    canal.is_closed = False
    conexion.channel.return_value = canal
    mock_conn_cls.return_value = conexion

    pub = publisher.RabbitMqConsumoPublisher()
    mensaje = ConsumoRegistradoMensaje(
        monto_consumido=10.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    pub.publicar_consumo(mensaje)
    canal.basic_publish.assert_called_once()
    pub.cerrar()


@patch("infrastructure.rabbitmq.publisher.pika.BlockingConnection")
def test_publicar_consumo_reintenta_tras_fallo(mock_conn_cls):
    conexion = MagicMock()
    conexion.is_closed = False
    conexion.is_open = True
    canal = MagicMock()
    canal.is_closed = False
    canal.basic_publish.side_effect = [
        pika_exceptions.AMQPConnectionError(),
        None,
    ]
    conexion.channel.return_value = canal
    mock_conn_cls.return_value = conexion

    pub = publisher.RabbitMqConsumoPublisher()
    mensaje = ConsumoRegistradoMensaje(
        monto_consumido=10.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    pub.publicar_consumo(mensaje)
    assert canal.basic_publish.call_count == 2


@patch("infrastructure.rabbitmq.publisher.pika.BlockingConnection")
def test_publicar_consumo_falla_definitivo(mock_conn_cls):
    conexion = MagicMock()
    conexion.is_closed = False
    conexion.is_open = True
    canal = MagicMock()
    canal.is_closed = False
    canal.basic_publish.side_effect = pika_exceptions.AMQPConnectionError()
    conexion.channel.return_value = canal
    mock_conn_cls.return_value = conexion

    pub = publisher.RabbitMqConsumoPublisher()
    mensaje = ConsumoRegistradoMensaje(
        monto_consumido=10.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    with pytest.raises(pika_exceptions.AMQPConnectionError):
        pub.publicar_consumo(mensaje)


def test_publicar_recompensa():
    canal = MagicMock()
    pub = publisher.RabbitMqRecompensaPublisher(canal)
    evento = RecompensaProcesadaMensaje(
        transaccion_id=uuid4(),
        numero_tarjeta="4111111111111111",
        puntos_abonados=5,
        saldo_total=5,
        codigo_restaurante="REST-01",
        procesado_en=datetime.now(timezone.utc),
    )
    pub.publicar_recompensa(evento)
    canal.basic_publish.assert_called_once()


@patch("infrastructure.rabbitmq.consumer.pika.BlockingConnection")
def test_consumir_cola_mensaje_valido(mock_conn_cls):
    conexion = MagicMock()
    canal = MagicMock()
    mock_conn_cls.return_value = conexion
    conexion.channel.return_value = canal

    callback_guardado = None

    def registrar_consumo(*_args, on_message_callback, **_kwargs):
        nonlocal callback_guardado
        callback_guardado = on_message_callback

    canal.basic_consume.side_effect = registrar_consumo

    def iniciar_consumo():
        cuerpo = json.dumps(
            {
                "monto_consumido": 50.0,
                "numero_tarjeta": "4111111111111111",
                "codigo_restaurante": "REST-01",
                "fecha_hora": datetime.now(timezone.utc).isoformat(),
            }
        ).encode()
        metodo = MagicMock(delivery_tag=7)
        callback_guardado(canal, metodo, None, cuerpo)
        raise KeyboardInterrupt()

    canal.start_consuming.side_effect = iniciar_consumo

    procesados = []

    consumer.consumir_cola(
        "cola.test",
        ConsumoRegistradoMensaje,
        lambda msg: procesados.append(msg),
    )

    assert len(procesados) == 1
    canal.basic_ack.assert_called_once()


@patch("infrastructure.rabbitmq.consumer.pika.BlockingConnection")
def test_consumir_cola_mensaje_invalido(mock_conn_cls, capsys):
    conexion = MagicMock()
    canal = MagicMock()
    mock_conn_cls.return_value = conexion
    conexion.channel.return_value = canal

    callback_guardado = None

    def registrar_consumo(*_args, on_message_callback, **_kwargs):
        nonlocal callback_guardado
        callback_guardado = on_message_callback

    canal.basic_consume.side_effect = registrar_consumo

    def iniciar_consumo():
        metodo = MagicMock(delivery_tag=8)
        callback_guardado(canal, metodo, None, b"{no-json")
        raise KeyboardInterrupt()

    canal.start_consuming.side_effect = iniciar_consumo

    consumer.consumir_cola("cola.test", ConsumoRegistradoMensaje, lambda _m: None)
    canal.basic_nack.assert_called_once()
    assert "[ERROR]" in capsys.readouterr().out


@patch("infrastructure.rabbitmq.consumer.pika.BlockingConnection")
def test_consumir_cola_validacion_pydantic(mock_conn_cls):
    conexion = MagicMock()
    canal = MagicMock()
    mock_conn_cls.return_value = conexion
    conexion.channel.return_value = canal

    callback_guardado = None

    def registrar_consumo(*_args, on_message_callback, **_kwargs):
        nonlocal callback_guardado
        callback_guardado = on_message_callback

    canal.basic_consume.side_effect = registrar_consumo

    def iniciar_consumo():
        cuerpo = json.dumps({"numero_tarjeta": "x"}).encode()
        metodo = MagicMock(delivery_tag=9)
        callback_guardado(canal, metodo, None, cuerpo)
        raise KeyboardInterrupt()

    canal.start_consuming.side_effect = iniciar_consumo

    consumer.consumir_cola("cola.test", ConsumoRegistradoMensaje, lambda _m: None)
    canal.basic_nack.assert_called_once()
