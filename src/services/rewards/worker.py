from application.use_cases.process_reward import ProcesarRecompensaUseCase
from common.constants import QUEUE_REWARDS
from common.schemas import ConsumoRegistradoMensaje
from infrastructure.persistence.factory import crear_repositorio_cuentas
from infrastructure.rabbitmq.factory import crear_recompensa_publisher
from infrastructure.rabbitmq.runner import iniciar_consumidor


def crear_caso_uso() -> ProcesarRecompensaUseCase:
    return ProcesarRecompensaUseCase(
        repositorio=crear_repositorio_cuentas(),
        recompensa_publisher=crear_recompensa_publisher(),
    )


def main() -> None:
    caso_uso = crear_caso_uso()

    def manejar(mensaje: ConsumoRegistradoMensaje) -> None:
        resultado = caso_uso.ejecutar(mensaje)
        if resultado.ya_existia:
            print(f"[INFO] Transacción duplicada ignorada: {mensaje.transaccion_id}")
        else:
            print(
                f"[RECOMPENSA] Tarjeta ****{mensaje.numero_tarjeta[-4:]}: "
                f"+{resultado.puntos_abonados} pts → saldo {resultado.saldo_total}"
            )

    iniciar_consumidor(QUEUE_REWARDS, ConsumoRegistradoMensaje, manejar)


if __name__ == "__main__":
    main()
 