from application.ports import CuentaRecompensasRepository
from domain.rewards import CuentaRecompensas


class MemoriaCuentaRecompensasRepository(CuentaRecompensasRepository):
    def __init__(self) -> None:
        self._cuentas: dict[str, CuentaRecompensas] = {}

    def obtener_o_crear(self, numero_tarjeta: str) -> CuentaRecompensas:
        if numero_tarjeta not in self._cuentas:
            self._cuentas[numero_tarjeta] = CuentaRecompensas(numero_tarjeta=numero_tarjeta)
        return self._cuentas[numero_tarjeta]

    def guardar(self, cuenta: CuentaRecompensas) -> None:
        self._cuentas[cuenta.numero_tarjeta] = cuenta

    def consultar_saldo(self, numero_tarjeta: str) -> int | None:
        cuenta = self._cuentas.get(numero_tarjeta.replace(" ", "").replace("-", ""))
        return cuenta.saldo_puntos if cuenta else None
