from datetime import datetime, timezone

from application.ports import CuentaRecompensasRepository, RecompensaPublisher
from common.schemas import ConsumoRegistradoMensaje, RecompensaProcesadaMensaje
from domain.rewards import abonar_puntos


class ProcesarRecompensaUseCase:
    def __init__(
        self,
        repositorio: CuentaRecompensasRepository,
        recompensa_publisher: RecompensaPublisher | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._recompensa_publisher = recompensa_publisher

    def ejecutar(self, mensaje: ConsumoRegistradoMensaje):
        cuenta = self._repositorio.obtener_o_crear(mensaje.numero_tarjeta)
        resultado = abonar_puntos(
            cuenta=cuenta,
            transaccion_id=mensaje.transaccion_id,
            monto_consumido=mensaje.monto_consumido,
            codigo_restaurante=mensaje.codigo_restaurante,
            email_cliente=str(mensaje.email_cliente) if mensaje.email_cliente else None,
        )
        self._repositorio.guardar(cuenta)

        if resultado.ya_existia:
            return resultado

        if self._recompensa_publisher is not None:
            evento = RecompensaProcesadaMensaje(
                transaccion_id=resultado.transaccion_id,
                numero_tarjeta=resultado.numero_tarjeta,
                puntos_abonados=resultado.puntos_abonados,
                saldo_total=resultado.saldo_total,
                codigo_restaurante=resultado.codigo_restaurante,
                procesado_en=datetime.now(timezone.utc),
                email_cliente=resultado.email_cliente,
                enviar_notificacion_email=bool(resultado.email_cliente),
            )
            self._recompensa_publisher.publicar_recompensa(evento)

        return resultado
