import os
from pathlib import Path

import pika


def cargar_dotenv() -> None:
    raiz = Path(__file__).resolve().parents[3]
    env_path = raiz / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def obtener_parametros() -> pika.ConnectionParameters:
    cargar_dotenv()
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_secret = os.getenv("RABBITMQ_PASSWORD")
    if rabbitmq_secret is None:
        rabbitmq_secret = os.getenv("RABBITMQ_PASS", "guest")
    virtual_host = os.getenv("RABBITMQ_VHOST", "/")
    heartbeat = int(os.getenv("RABBITMQ_HEARTBEAT", "0"))
    blocked_timeout = float(os.getenv("RABBITMQ_BLOCKED_TIMEOUT", "120"))
    return pika.ConnectionParameters(
        host=host,
        port=port,
        virtual_host=virtual_host,
        credentials=pika.PlainCredentials(user, rabbitmq_secret),
        heartbeat=heartbeat,
        blocked_connection_timeout=blocked_timeout,
    )


def declarar_topologia(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    from common.constants import (
        EXCHANGE_LOYALTY,
        QUEUE_NOTIFICATIONS,
        QUEUE_REWARDS,
        ROUTING_CONSUMO_REGISTRADO,
        ROUTING_RECOMPENSA_PROCESADA,
    )

    channel.exchange_declare(
        exchange=EXCHANGE_LOYALTY,
        exchange_type="topic",
        durable=True,
    )
    channel.queue_declare(queue=QUEUE_REWARDS, durable=True)
    channel.queue_bind(
        exchange=EXCHANGE_LOYALTY,
        queue=QUEUE_REWARDS,
        routing_key=ROUTING_CONSUMO_REGISTRADO,
    )
    channel.queue_declare(queue=QUEUE_NOTIFICATIONS, durable=True)
    channel.queue_bind(
        exchange=EXCHANGE_LOYALTY,
        queue=QUEUE_NOTIFICATIONS,
        routing_key=ROUTING_RECOMPENSA_PROCESADA,
    )
