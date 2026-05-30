from uuid import uuid4

from domain.rewards import abonar_puntos, calcular_puntos, CuentaRecompensas


def test_calcular_puntos_proporcional():
    assert calcular_puntos(100.0) == 10
    assert calcular_puntos(5.0) == 1


def test_abonar_puntos_actualiza_saldo():
    cuenta = CuentaRecompensas(numero_tarjeta="4111111111111111")
    tx = uuid4()
    resultado = abonar_puntos(cuenta, tx, 50.0, "REST-01")
    assert resultado.puntos_abonados == 5
    assert resultado.saldo_total == 5
    assert not resultado.ya_existia


def test_abonar_es_idempotente():
    cuenta = CuentaRecompensas(numero_tarjeta="4111111111111111")
    tx = uuid4()
    abonar_puntos(cuenta, tx, 50.0, "REST-01")
    duplicado = abonar_puntos(cuenta, tx, 50.0, "REST-01")
    assert duplicado.ya_existia
    assert duplicado.puntos_abonados == 0
    assert cuenta.saldo_puntos == 5
