import os

from application.ports import NotificadorRecompensa
from infrastructure.notifications.console_notifier import ConsolaNotificador
from infrastructure.notifications.email_notifier import EmailNotificador
from infrastructure.rabbitmq.connection import cargar_dotenv


def crear_notificador() -> NotificadorRecompensa:
    cargar_dotenv()
    canal = os.getenv("NOTIFICATION_CHANNEL", "email").lower()
    if canal == "console":
        return ConsolaNotificador()
    return EmailNotificador()
