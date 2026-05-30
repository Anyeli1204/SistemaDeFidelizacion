from application.ports import NotificadorRecompensa
from common.schemas import RecompensaProcesadaMensaje


class NotificarRecompensaUseCase:
    def __init__(self, notificador: NotificadorRecompensa) -> None:
        self._notificador = notificador

    def ejecutar(self, mensaje: RecompensaProcesadaMensaje) -> None:
        if not mensaje.email_cliente:
            return
        self._notificador.notificar(
            numero_tarjeta=mensaje.numero_tarjeta,
            puntos_abonados=mensaje.puntos_abonados,
            saldo_total=mensaje.saldo_total,
            procesado_en=mensaje.procesado_en,
            email_cliente=mensaje.email_cliente,
        )
