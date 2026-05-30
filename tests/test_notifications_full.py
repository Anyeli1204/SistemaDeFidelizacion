from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from application.use_cases.notify_reward import NotificarRecompensaUseCase
from common.schemas import RecompensaProcesadaMensaje
from infrastructure.notifications.console_notifier import ConsolaNotificador
from infrastructure.notifications.email_notifier import (
    EmailNotificador,
    _correo_cliente,
    _destinatarios,
)
from infrastructure.notifications.factory import crear_notificador
from uuid import uuid4


def test_correo_cliente_y_destinatarios(monkeypatch):
    monkeypatch.setenv("NOTIFICATION_EMAIL_DOMAIN", "lab.test")
    assert _correo_cliente("4111111111111111").endswith("@lab.test")

    assert _destinatarios("4111111111111111", "real@test.com") == ["real@test.com"]

    monkeypatch.delenv("EMAIL_TO_OVERRIDE", raising=False)
    monkeypatch.setenv("EMAIL_TO_OVERRIDE", "a@test.com,b@test.com")
    assert _destinatarios("4111111111111111", None) == ["a@test.com", "b@test.com"]


def test_consola_notificador(capsys):
    notificador = ConsolaNotificador()
    notificador.notificar(
        numero_tarjeta="4111111111111111",
        puntos_abonados=3,
        saldo_total=8,
        procesado_en=datetime(2026, 5, 27, tzinfo=timezone.utc),
        email_cliente="x@test.com",
    )
    assert "NOTIFICACIÓN" in capsys.readouterr().out


def test_factory_canales(monkeypatch):
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "console")
    assert isinstance(crear_notificador(), ConsolaNotificador)

    monkeypatch.setenv("NOTIFICATION_CHANNEL", "email")
    assert isinstance(crear_notificador(), EmailNotificador)


@patch("infrastructure.notifications.email_notifier.smtplib.SMTP")
def test_email_notifier_smtp(mock_smtp_cls, tmp_path, monkeypatch):
    log = tmp_path / "emails.log"
    monkeypatch.setenv("EMAIL_SMTP_HOST", "smtp.test")
    monkeypatch.setenv("EMAIL_SMTP_USER", "user")
    monkeypatch.setenv("EMAIL_SMTP_PASSWORD", "pass")
    monkeypatch.setenv("EMAIL_SMTP_TLS", "true")

    servidor = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = servidor

    notificador = EmailNotificador(log_path=log)
    notificador.notificar(
        numero_tarjeta="4111111111111111",
        puntos_abonados=5,
        saldo_total=15,
        procesado_en=datetime(2026, 5, 27, 20, 0, tzinfo=timezone.utc),
        email_cliente="cliente@test.com",
    )
    servidor.starttls.assert_called_once()
    servidor.login.assert_called_once()
    servidor.sendmail.assert_called_once()


@patch("infrastructure.notifications.email_notifier.smtplib.SMTP")
def test_email_notifier_smtp_sin_tls_ni_login(mock_smtp_cls, tmp_path, monkeypatch):
    log = tmp_path / "emails.log"
    monkeypatch.setenv("EMAIL_SMTP_HOST", "smtp.test")
    monkeypatch.setenv("EMAIL_SMTP_TLS", "false")
    monkeypatch.delenv("EMAIL_SMTP_USER", raising=False)

    servidor = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = servidor

    notificador = EmailNotificador(log_path=log)
    notificador.notificar(
        numero_tarjeta="4111111111111111",
        puntos_abonados=1,
        saldo_total=1,
        procesado_en=datetime(2026, 5, 27, tzinfo=timezone.utc),
    )
    servidor.starttls.assert_not_called()
    servidor.login.assert_not_called()


def test_notificar_recompensa_con_y_sin_email(tmp_path):
    log = tmp_path / "emails.log"
    notificador = EmailNotificador(log_path=log)
    caso = NotificarRecompensaUseCase(notificador)

    sin_email = RecompensaProcesadaMensaje(
        transaccion_id=uuid4(),
        numero_tarjeta="4111111111111111",
        puntos_abonados=5,
        saldo_total=5,
        codigo_restaurante="REST-01",
        procesado_en=datetime.now(timezone.utc),
        email_cliente=None,
    )
    caso.ejecutar(sin_email)
    assert not log.exists() or log.read_text(encoding="utf-8") == ""

    con_email = sin_email.model_copy(update={"email_cliente": "cliente@test.com"})
    caso.ejecutar(con_email)
    assert "cliente@test.com" in log.read_text(encoding="utf-8")
