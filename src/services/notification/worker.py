import os

from application.use_cases.notify_reward import NotificarRecompensaUseCase
from infrastructure.rabbitmq.connection import cargar_dotenv
from common.constants import QUEUE_NOTIFICATIONS
from common.schemas import RecompensaProcesadaMensaje
from infrastructure.notifications.factory import crear_notificador
from infrastructure.rabbitmq.runner import iniciar_consumidor


def main() -> None:
    cargar_dotenv()
    notificador = crear_notificador()
    print(f"[*] Canal de notificación: {os.getenv('NOTIFICATION_CHANNEL', 'email')}")
    caso_uso = NotificarRecompensaUseCase(notificador)

    def manejar(mensaje: RecompensaProcesadaMensaje) -> None:
        caso_uso.ejecutar(mensaje)

    iniciar_consumidor(QUEUE_NOTIFICATIONS, RecompensaProcesadaMensaje, manejar)


if __name__ == "__main__":
    main()
