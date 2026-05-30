from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.use_cases.process_reward import ProcesarRecompensaUseCase
from application.use_cases.register_consumption import RegistrarConsumoUseCase
from common.schemas import ConsumoRegistradoMensaje
from domain.consumption import Consumo, ConsumoInvalidoError, validar_consumo
from infrastructure.persistence.memory_accounts import MemoriaCuentaRecompensasRepository
from tests.test_use_cases import FakeConsumoPublisher


def test_validar_consumo_errores():
    base = Consumo(
        transaccion_id=uuid4(),
        monto_consumido=0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    with pytest.raises(ConsumoInvalidoError):
        validar_consumo(base)

    with pytest.raises(ConsumoInvalidoError):
        validar_consumo(
            Consumo(
                transaccion_id=uuid4(),
                monto_consumido=10,
                numero_tarjeta="",
                codigo_restaurante="REST-01",
                fecha_hora=datetime.now(timezone.utc),
            )
        )

    with pytest.raises(ConsumoInvalidoError):
        validar_consumo(
            Consumo(
                transaccion_id=uuid4(),
                monto_consumido=10,
                numero_tarjeta="4111111111111111",
                codigo_restaurante="",
                fecha_hora=datetime.now(timezone.utc),
            )
        )


def test_registrar_consumo_normaliza_email():
    fake = FakeConsumoPublisher()
    caso = RegistrarConsumoUseCase(fake)
    caso.ejecutar(
        25.0,
        "4111111111111111",
        "rest-01",
        email_cliente="  Cliente@Mail.COM ",
    )
    assert fake.mensajes[0].email_cliente == "cliente@mail.com"


def test_procesar_recompensa_idempotente_sin_publicar():
    repo = MemoriaCuentaRecompensasRepository()
    publicador = Mock()
    caso = ProcesarRecompensaUseCase(repo, publicador)
    mensaje = ConsumoRegistradoMensaje(
        transaccion_id=uuid4(),
        monto_consumido=30.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
    )
    caso.ejecutar(mensaje)
    resultado = caso.ejecutar(mensaje)
    assert resultado.ya_existia
    publicador.publicar_recompensa.assert_called_once()
