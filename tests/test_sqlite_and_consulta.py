import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from application.use_cases.process_reward import ProcesarRecompensaUseCase
from common.schemas import ConsumoRegistradoMensaje
from domain.rewards import CuentaRecompensas
from infrastructure.persistence.sqlite_accounts import SqliteCuentaRecompensasRepository
from services.consulta import app as consulta_app


def test_sqlite_cuenta_ciclo_completo(tmp_path):
    db = tmp_path / "cuentas.db"
    repo = SqliteCuentaRecompensasRepository(db)

    cuenta = repo.obtener_o_crear("4111111111111111")
    assert cuenta.saldo_puntos == 0

    cuenta.saldo_puntos = 15
    cuenta.email_cliente = "cliente@test.com"
    cuenta.transacciones_procesadas.add(uuid4())
    repo.guardar(cuenta)

    recuperada = repo.obtener_o_crear("4111111111111111")
    assert recuperada.saldo_puntos == 15
    assert recuperada.email_cliente == "cliente@test.com"
    assert repo.consultar_saldo("4111 1111-1111 1111") == 15
    assert repo.consultar_saldo("9999999999999999") is None


def test_sqlite_migracion_columna_email(tmp_path):
    db = tmp_path / "legacy.db"
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE cuentas (
                numero_tarjeta TEXT PRIMARY KEY,
                saldo_puntos INTEGER NOT NULL DEFAULT 0,
                transacciones TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
    repo = SqliteCuentaRecompensasRepository(db)
    cuenta = repo.obtener_o_crear("4111111111111111")
    assert cuenta.email_cliente is None


def test_consulta_api_saldo_y_health(tmp_path, monkeypatch):
    db = tmp_path / "cuentas.db"
    repo = SqliteCuentaRecompensasRepository(db)
    caso = ProcesarRecompensaUseCase(repo)
    caso.ejecutar(
        ConsumoRegistradoMensaje(
            monto_consumido=100.0,
            numero_tarjeta="4111111111111111",
            codigo_restaurante="REST-01",
            fecha_hora=datetime.now(timezone.utc),
        )
    )

    monkeypatch.setattr(consulta_app, "_repositorio", repo)
    client = TestClient(consulta_app.app)

    ok = client.get("/api/cuentas/4111111111111111/saldo")
    assert ok.status_code == 200
    assert ok.json()["saldo_puntos"] == 10

    missing = client.get("/api/cuentas/9999999999999999/saldo")
    assert missing.status_code == 404

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["servicio"] == "consulta-puntos"

    consulta_app.app.openapi_schema = None
    schema = consulta_app.custom_openapi()
    assert schema["info"]["title"]
    assert consulta_app.custom_openapi() is schema
