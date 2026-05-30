import json
import os
import sqlite3
from pathlib import Path
from uuid import UUID

from application.ports import CuentaRecompensasRepository
from domain.rewards import CuentaRecompensas

DEFAULT_DB = Path(os.getenv("CUENTAS_DB_PATH", "data/cuentas.db"))


class SqliteCuentaRecompensasRepository(CuentaRecompensasRepository):
    def __init__(self, ruta_db: Path | None = None) -> None:
        self._ruta = ruta_db or DEFAULT_DB
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conexion(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._ruta)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._conexion() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cuentas (
                    numero_tarjeta TEXT PRIMARY KEY,
                    saldo_puntos INTEGER NOT NULL DEFAULT 0,
                    transacciones TEXT NOT NULL DEFAULT '[]',
                    email_cliente TEXT
                )
                """
            )
            columnas = {
                fila[1] for fila in conn.execute("PRAGMA table_info(cuentas)").fetchall()
            }
            if "email_cliente" not in columnas:
                conn.execute("ALTER TABLE cuentas ADD COLUMN email_cliente TEXT")

    def obtener_o_crear(self, numero_tarjeta: str) -> CuentaRecompensas:
        with self._conexion() as conn:
            fila = conn.execute(
                "SELECT * FROM cuentas WHERE numero_tarjeta = ?",
                (numero_tarjeta,),
            ).fetchone()
            if fila:
                return self._desde_fila(fila)
            conn.execute(
                """
                INSERT INTO cuentas (numero_tarjeta, saldo_puntos, transacciones, email_cliente)
                VALUES (?, 0, '[]', NULL)
                """,
                (numero_tarjeta,),
            )
            return CuentaRecompensas(numero_tarjeta=numero_tarjeta)

    def guardar(self, cuenta: CuentaRecompensas) -> None:
        transacciones = [str(t) for t in cuenta.transacciones_procesadas]
        with self._conexion() as conn:
            conn.execute(
                """
                INSERT INTO cuentas (numero_tarjeta, saldo_puntos, transacciones, email_cliente)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(numero_tarjeta) DO UPDATE SET
                    saldo_puntos = excluded.saldo_puntos,
                    transacciones = excluded.transacciones,
                    email_cliente = excluded.email_cliente
                """,
                (
                    cuenta.numero_tarjeta,
                    cuenta.saldo_puntos,
                    json.dumps(transacciones),
                    cuenta.email_cliente,
                ),
            )

    def consultar_saldo(self, numero_tarjeta: str) -> int | None:
        tarjeta = numero_tarjeta.replace(" ", "").replace("-", "")
        with self._conexion() as conn:
            fila = conn.execute(
                "SELECT saldo_puntos FROM cuentas WHERE numero_tarjeta = ?",
                (tarjeta,),
            ).fetchone()
        return int(fila["saldo_puntos"]) if fila else None

    @staticmethod
    def _desde_fila(fila: sqlite3.Row) -> CuentaRecompensas:
        ids = {UUID(t) for t in json.loads(fila["transacciones"])}
        email = fila["email_cliente"]
        return CuentaRecompensas(
            numero_tarjeta=fila["numero_tarjeta"],
            saldo_puntos=int(fila["saldo_puntos"]),
            email_cliente=email if email else None,
            transacciones_procesadas=ids,
        )
