from application.ports import CuentaRecompensasRepository
from infrastructure.persistence.sqlite_accounts import SqliteCuentaRecompensasRepository


def crear_repositorio_cuentas() -> CuentaRecompensasRepository:
    return SqliteCuentaRecompensasRepository()
