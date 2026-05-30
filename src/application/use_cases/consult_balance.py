from application.ports import CuentaRecompensasRepository
from domain.rewards import CuentaNoEncontradaError, SaldoConsultado


class ConsultarSaldoUseCase:
    def __init__(self, repositorio: CuentaRecompensasRepository) -> None:
        self._repositorio = repositorio

    def ejecutar(self, numero_tarjeta: str) -> SaldoConsultado:
        tarjeta = numero_tarjeta.replace(" ", "").replace("-", "")
        saldo = self._repositorio.consultar_saldo(tarjeta)
        if saldo is None:
            raise CuentaNoEncontradaError(tarjeta)
        return SaldoConsultado(numero_tarjeta=tarjeta, saldo_puntos=saldo)
