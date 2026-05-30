from __future__ import annotations

import os
from pathlib import Path

import pytest


def _cargar_dotenv() -> None:
    raiz = Path(__file__).resolve().parent.parent
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
        if key:
            os.environ[key] = value


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: prueba contra RabbitMQ real (requiere .env y broker del curso)",
    )


@pytest.fixture(scope="session", autouse=True)
def _dotenv_para_tests() -> None:
    _cargar_dotenv()


@pytest.fixture(scope="session")
def broker_disponible() -> bool:
    import pika

    from infrastructure.rabbitmq.connection import obtener_parametros

    try:
        conexion = pika.BlockingConnection(obtener_parametros())
        conexion.close()
        return True
    except Exception:
        return False


@pytest.fixture
def require_broker(broker_disponible: bool) -> None:
    if not broker_disponible:
        pytest.skip(
            "RabbitMQ no disponible: revisa .env (RABBITMQ_HOST, USER, PASSWORD) y la red"
        )
