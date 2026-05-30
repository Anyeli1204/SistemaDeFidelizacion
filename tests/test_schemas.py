from datetime import datetime, timezone

import pytest

from common.schemas import ConsumoRegistradoMensaje


def test_mensaje_valido():
    msg = ConsumoRegistradoMensaje(
        monto_consumido=120.5,
        numero_tarjeta="4111 1111 1111 1111",
        codigo_restaurante="rest-lima-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    assert msg.numero_tarjeta == "4111111111111111"
    assert msg.codigo_restaurante == "REST-LIMA-01"


def test_monto_negativo_rechazado():
    with pytest.raises(ValueError):
        ConsumoRegistradoMensaje(
            monto_consumido=-1,
            numero_tarjeta="4111111111111111",
            codigo_restaurante="REST-01",
            fecha_hora=datetime.now(timezone.utc),
        )


def test_tarjeta_con_letras_rechazada():
    with pytest.raises(ValueError, match="solo dígitos"):
        ConsumoRegistradoMensaje(
            monto_consumido=10.0,
            numero_tarjeta="4111ABCD11111111",
            codigo_restaurante="REST-01",
            fecha_hora=datetime.now(timezone.utc),
        )
