from uuid import uuid4

from domain.rewards import (
    CuentaRecompensas,
    abonar_puntos,
    registrar_email_si_vacio,
)


def test_registrar_email_solo_la_primera_vez():
    cuenta = CuentaRecompensas(numero_tarjeta="4111111111111111")
    assert registrar_email_si_vacio(cuenta, "cliente@mail.com") is True
    assert cuenta.email_cliente == "cliente@mail.com"
    assert registrar_email_si_vacio(cuenta, "otro@mail.com") is False
    assert cuenta.email_cliente == "cliente@mail.com"


def test_notificacion_solo_cuando_email_nuevo():
    cuenta = CuentaRecompensas(numero_tarjeta="4111111111111111")
    r1 = abonar_puntos(
        cuenta, uuid4(), 50.0, "REST-01", email_cliente="nuevo@mail.com"
    )
    assert r1.email_registrado_ahora is True

    r2 = abonar_puntos(
        cuenta, uuid4(), 50.0, "REST-01", email_cliente="otro@mail.com"
    )
    assert r2.email_registrado_ahora is False
