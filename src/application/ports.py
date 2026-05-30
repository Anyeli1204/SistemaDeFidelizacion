from abc import ABC, abstractmethod
from datetime import datetime

from common.schemas import ConsumoRegistradoMensaje, RecompensaProcesadaMensaje
from domain.rewards import CuentaRecompensas


class ConsumoPublisher(ABC):
    @abstractmethod
    def publicar_consumo(self, mensaje: ConsumoRegistradoMensaje) -> None:
        pass


class RecompensaPublisher(ABC):
    @abstractmethod
    def publicar_recompensa(self, mensaje: RecompensaProcesadaMensaje) -> None:
        pass


class CuentaRecompensasRepository(ABC):
    @abstractmethod
    def obtener_o_crear(self, numero_tarjeta: str) -> CuentaRecompensas:
        pass

    @abstractmethod
    def guardar(self, cuenta: CuentaRecompensas) -> None:
        pass

    @abstractmethod
    def consultar_saldo(self, numero_tarjeta: str) -> int | None:
        pass


class NotificadorRecompensa(ABC):
    @abstractmethod
    def notificar(
        self,
        numero_tarjeta: str,
        puntos_abonados: int,
        saldo_total: int,
        procesado_en: datetime,
        email_cliente: str | None = None,
    ) -> None:
        pass
