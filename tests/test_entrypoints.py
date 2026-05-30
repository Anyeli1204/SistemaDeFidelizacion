import runpy
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

from common.schemas import ConsumoRegistradoMensaje, RecompensaProcesadaMensaje


@patch("uvicorn.run")
def test_restaurant_main(mock_run, monkeypatch):
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    runpy.run_module("services.restaurant.__main__", run_name="__main__")
    mock_run.assert_called_once()


@patch("uvicorn.run")
def test_consulta_main(mock_run, monkeypatch):
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    runpy.run_module("services.consulta.__main__", run_name="__main__")
    mock_run.assert_called_once()


@patch("services.rewards.worker.main")
def test_rewards_package_invoca_worker(mock_main):
    from services.rewards import __main__ as rewards_entry

    rewards_entry.main()
    mock_main.assert_called_once()


@patch("services.notification.worker.main")
def test_notification_package_invoca_worker(mock_main):
    from services.notification import __main__ as notification_entry

    notification_entry.main()
    mock_main.assert_called_once()


def test_rewards_worker_manejadores(capsys):
    from services.rewards import worker

    mensaje = ConsumoRegistradoMensaje(
        monto_consumido=50.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )

    caso = MagicMock()
    ok = MagicMock(ya_existia=False, puntos_abonados=5, saldo_total=5)
    dup = MagicMock(ya_existia=True)
    caso.ejecutar.side_effect = [ok, dup]

    with patch.object(worker, "crear_caso_uso", return_value=caso):
        with patch.object(worker, "iniciar_consumidor") as mock_consumir:

            def ejecutar(_cola, _modelo, manejador):
                manejador(mensaje)
                manejador(mensaje)

            mock_consumir.side_effect = ejecutar
            worker.main()

    salida = capsys.readouterr().out
    assert "[RECOMPENSA]" in salida
    assert "duplicada" in salida


def test_notification_worker_main(monkeypatch):
    from services.notification import worker

    mensaje = RecompensaProcesadaMensaje(
        transaccion_id=uuid4(),
        numero_tarjeta="4111111111111111",
        puntos_abonados=5,
        saldo_total=5,
        codigo_restaurante="REST-01",
        procesado_en=datetime.now(timezone.utc),
        email_cliente="a@test.com",
    )

    caso = MagicMock()
    notificador = MagicMock()
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "console")

    with patch.object(worker, "crear_notificador", return_value=notificador):
        with patch.object(worker, "NotificarRecompensaUseCase", return_value=caso):
            with patch.object(worker, "iniciar_consumidor") as mock_consumir:
                mock_consumir.side_effect = lambda _c, _m, h: h(mensaje)
                worker.main()

    caso.ejecutar.assert_called_once_with(mensaje)
