from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from common.schemas import ConsumoRegistradoMensaje
from services.restaurant import app as restaurant_app


@patch("services.restaurant.app._obtener_caso_uso")
def test_registrar_consumo_endpoint(mock_caso):
    mensaje = ConsumoRegistradoMensaje(
        transaccion_id=uuid4(),
        monto_consumido=50.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    mock_caso.return_value.ejecutar.return_value = mensaje

    client = TestClient(restaurant_app.app)
    response = client.post(
        "/api/consumos",
        json={
            "monto_consumido": 50.0,
            "numero_tarjeta": "4111111111111111",
            "codigo_restaurante": "REST-01",
        },
    )
    assert response.status_code == 202
    assert "transaccion_id" in response.json()


@patch("services.restaurant.app.crear_consumo_publisher")
def test_obtener_caso_uso_singleton(mock_crear_publisher):
    restaurant_app._publisher = None
    instancia = MagicMock()
    mock_crear_publisher.return_value = instancia
    restaurant_app._obtener_caso_uso()
    restaurant_app._obtener_caso_uso()
    mock_crear_publisher.assert_called_once()
    assert restaurant_app._publisher is instancia
    restaurant_app._publisher = None


@patch("services.restaurant.app._obtener_caso_uso")
def test_registrar_consumo_error_validacion(mock_caso):
    mock_caso.return_value.ejecutar.side_effect = ValueError("monto inválido")
    client = TestClient(restaurant_app.app)
    response = client.post(
        "/api/consumos",
        json={
            "monto_consumido": -1,
            "numero_tarjeta": "4111111111111111",
            "codigo_restaurante": "REST-01",
        },
    )
    assert response.status_code == 422 or response.status_code == 400


@patch("services.restaurant.app._obtener_caso_uso")
def test_registrar_consumo_error_broker(mock_caso):
    mock_caso.return_value.ejecutar.side_effect = RuntimeError("broker caído")
    client = TestClient(restaurant_app.app)
    response = client.post(
        "/api/consumos",
        json={
            "monto_consumido": 50.0,
            "numero_tarjeta": "4111111111111111",
            "codigo_restaurante": "REST-01",
        },
    )
    assert response.status_code == 503


def test_health_y_openapi_restaurante():
    client = TestClient(restaurant_app.app)
    health = client.get("/health")
    assert health.status_code == 200

    restaurant_app.app.openapi_schema = None
    schema = restaurant_app.custom_openapi()
    assert "x-logo" in schema["info"]
    assert restaurant_app.custom_openapi() is schema
