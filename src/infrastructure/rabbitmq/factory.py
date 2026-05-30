import pika

from application.ports import ConsumoPublisher, RecompensaPublisher
from infrastructure.rabbitmq.connection import declarar_topologia, obtener_parametros
from infrastructure.rabbitmq.publisher import RabbitMqConsumoPublisher, RabbitMqRecompensaPublisher


def crear_consumo_publisher() -> ConsumoPublisher:
    return RabbitMqConsumoPublisher()


def crear_recompensa_publisher() -> RecompensaPublisher:
    connection = pika.BlockingConnection(obtener_parametros())
    channel = connection.channel()
    declarar_topologia(channel)
    return RabbitMqRecompensaPublisher(channel)
