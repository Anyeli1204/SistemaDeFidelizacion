from datetime import datetime

from application.ports import NotificadorRecompensa


class ConsolaNotificador(NotificadorRecompensa):
    def notificar(
        self,
        numero_tarjeta: str,
        puntos_abonados: int,
        saldo_total: int,
        procesado_en: datetime,
        email_cliente: str | None = None,
    ) -> None:
        tarjeta_enmascarada = f"****{numero_tarjeta[-4:]}"
        print(
            f"[NOTIFICACIÓN] Tarjeta {tarjeta_enmascarada}: "
            f"+{puntos_abonados} puntos. Saldo: {saldo_total}. "
            f"({procesado_en.isoformat()})"
        )
