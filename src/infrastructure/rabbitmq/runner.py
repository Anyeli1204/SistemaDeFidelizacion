from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel

from infrastructure.rabbitmq.consumer import consumir_cola

T = TypeVar("T", bound=BaseModel)


def iniciar_consumidor(
    nombre_cola: str,
    modelo: type[T],
    manejador: Callable[[T], None],
) -> None:
    consumir_cola(nombre_cola, modelo, manejador)
