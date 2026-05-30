from datetime import datetime, timezone
from uuid import uuid4

from application.use_cases.consult_balance import ConsultarSaldoUseCase
from application.use_cases.process_reward import ProcesarRecompensaUseCase
from application.use_cases.register_consumption import RegistrarConsumoUseCase
from common.schemas import ConsumoRegistradoMensaje, RecompensaProcesadaMensaje
from domain.rewards import CuentaNoEncontradaError
from infrastructure.persistence.memory_accounts import MemoriaCuentaRecompensasRepository


class FakeConsumoPublisher:
    def __init__(self) -> None:
        self.mensajes: list[ConsumoRegistradoMensaje] = []

    def publicar_consumo(self, mensaje: ConsumoRegistradoMensaje) -> None:
        self.mensajes.append(mensaje)


class FakeRecompensaPublisher:
    def __init__(self) -> None:
        self.eventos: list[RecompensaProcesadaMensaje] = []

    def publicar_recompensa(self, mensaje: RecompensaProcesadaMensaje) -> None:
        self.eventos.append(mensaje)


def test_registrar_consumo_publica_mensaje():
    fake = FakeConsumoPublisher()
    caso = RegistrarConsumoUseCase(fake)
    resultado = caso.ejecutar(80.0, "4111111111111111", "REST-01")
    assert len(fake.mensajes) == 1
    assert fake.mensajes[0].transaccion_id == resultado.transaccion_id


def test_procesar_recompensa_abona_y_emite_evento():
    repo = MemoriaCuentaRecompensasRepository()
    eventos = FakeRecompensaPublisher()
    caso = ProcesarRecompensaUseCase(repo, eventos)
    mensaje = ConsumoRegistradoMensaje(
        transaccion_id=uuid4(),
        monto_consumido=100.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
        email_cliente="cliente@test.com",
    )
    resultado = caso.ejecutar(mensaje)
    assert resultado.puntos_abonados == 10
    assert len(eventos.eventos) == 1
    assert eventos.eventos[0].enviar_notificacion_email is True
    assert eventos.eventos[0].email_cliente == "cliente@test.com"
    assert repo.consultar_saldo("4111111111111111") == 10


def test_procesar_recompensa_reusa_email_persistido_para_nuevos_consumos():
    repo = MemoriaCuentaRecompensasRepository()
    eventos = FakeRecompensaPublisher()
    caso = ProcesarRecompensaUseCase(repo, eventos)

    primer_consumo = ConsumoRegistradoMensaje(
        transaccion_id=uuid4(),
        monto_consumido=100.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
        email_cliente="cliente@test.com",
    )
    caso.ejecutar(primer_consumo)

    segundo_consumo = ConsumoRegistradoMensaje(
        transaccion_id=uuid4(),
        monto_consumido=50.0,
        numero_tarjeta="4111111111111111",
        codigo_restaurante="REST-01",
        fecha_hora=datetime.now(timezone.utc),
        email_cliente=None,
    )
    caso.ejecutar(segundo_consumo)

    assert len(eventos.eventos) == 2
    assert eventos.eventos[1].email_cliente == "cliente@test.com"
    assert eventos.eventos[1].enviar_notificacion_email is True


def test_consultar_saldo_devuelve_puntos_del_cliente():
    repo = MemoriaCuentaRecompensasRepository()
    procesar = ProcesarRecompensaUseCase(repo)
    procesar.ejecutar(
        ConsumoRegistradoMensaje(
            transaccion_id=uuid4(),
            monto_consumido=120.0,
            numero_tarjeta="4111111111111111",
            codigo_restaurante="REST-01",
            fecha_hora=datetime.now(timezone.utc),
        )
    )

    resultado = ConsultarSaldoUseCase(repo).ejecutar("4111 1111-1111 1111")
    assert resultado.numero_tarjeta == "4111111111111111"
    assert resultado.saldo_puntos == 12


def test_consultar_saldo_cuenta_inexistente():
    repo = MemoriaCuentaRecompensasRepository()
    try:
        ConsultarSaldoUseCase(repo).ejecutar("9999999999999999")
        assert False, "debía lanzar CuentaNoEncontradaError"
    except CuentaNoEncontradaError as error:
        assert error.numero_tarjeta == "9999999999999999"
