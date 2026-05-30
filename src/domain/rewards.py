
from dataclasses import dataclass, field
from uuid import UUID

PUNTOS_POR_UNIDAD_MONETARIA = 0.1


class CuentaNoEncontradaError(LookupError):
    def __init__(self, numero_tarjeta: str) -> None:
        self.numero_tarjeta = numero_tarjeta
        super().__init__(f"Cuenta no encontrada para la tarjeta {numero_tarjeta}")


@dataclass(frozen=True)
class SaldoConsultado:
    numero_tarjeta: str
    saldo_puntos: int


@dataclass
class CuentaRecompensas:
    numero_tarjeta: str
    saldo_puntos: int = 0
    email_cliente: str | None = None
    transacciones_procesadas: set[UUID] = field(default_factory=set)


def calcular_puntos(monto_consumido: float) -> int:
    return max(1, int(monto_consumido * PUNTOS_POR_UNIDAD_MONETARIA))


def registrar_email_si_vacio(cuenta: CuentaRecompensas, email: str | None) -> bool:
    if not email or not email.strip():
        return False
    if cuenta.email_cliente:
        return False
    cuenta.email_cliente = email.strip().lower()
    return True


@dataclass(frozen=True)
class ResultadoAbono:
    transaccion_id: UUID
    numero_tarjeta: str
    puntos_abonados: int
    saldo_total: int
    codigo_restaurante: str
    ya_existia: bool = False
    email_registrado_ahora: bool = False
    email_cliente: str | None = None


def abonar_puntos(
    cuenta: CuentaRecompensas,
    transaccion_id: UUID,
    monto_consumido: float,
    codigo_restaurante: str,
    email_cliente: str | None = None,
) -> ResultadoAbono:
    email_nuevo = registrar_email_si_vacio(cuenta, email_cliente)

    if transaccion_id in cuenta.transacciones_procesadas:
        return ResultadoAbono(
            transaccion_id=transaccion_id,
            numero_tarjeta=cuenta.numero_tarjeta,
            puntos_abonados=0,
            saldo_total=cuenta.saldo_puntos,
            codigo_restaurante=codigo_restaurante,
            ya_existia=True,
            email_registrado_ahora=False,
            email_cliente=cuenta.email_cliente,
        )

    puntos = calcular_puntos(monto_consumido)
    cuenta.saldo_puntos += puntos
    cuenta.transacciones_procesadas.add(transaccion_id)
    return ResultadoAbono(
        transaccion_id=transaccion_id,
        numero_tarjeta=cuenta.numero_tarjeta,
        puntos_abonados=puntos,
        saldo_total=cuenta.saldo_puntos,
        codigo_restaurante=codigo_restaurante,
        email_registrado_ahora=email_nuevo,
        email_cliente=cuenta.email_cliente,
    )
