from datetime import datetime, timezone
from pathlib import Path

from infrastructure.notifications.email_notifier import EmailNotificador


def test_email_notifier_escribe_archivo(tmp_path):
    log = tmp_path / "emails.log"
    notificador = EmailNotificador(log_path=log)
    notificador.notificar(
        numero_tarjeta="4111111111111111",
        puntos_abonados=5,
        saldo_total=15,
        procesado_en=datetime(2026, 5, 27, 20, 0, tzinfo=timezone.utc),
    )
    contenido = log.read_text(encoding="utf-8")
    assert "cliente.1111@" in contenido
    assert "Se abonaron 5 puntos" in contenido
    assert "Saldo actual: 15 puntos" in contenido


def test_email_notifier_override_destino(tmp_path, monkeypatch):
    log = tmp_path / "emails.log"
    monkeypatch.setenv("EMAIL_TO_OVERRIDE", "miemail@example.com")
    notificador = EmailNotificador(log_path=log)
    notificador.notificar(
        numero_tarjeta="4111111111111111",
        puntos_abonados=5,
        saldo_total=15,
        procesado_en=datetime(2026, 5, 27, 20, 0, tzinfo=timezone.utc),
    )
    contenido = log.read_text(encoding="utf-8")
    assert "miemail@example.com" in contenido
