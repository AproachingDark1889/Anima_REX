import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

@dataclass
class Orden:
    tipo: str
    activo: str
    resultado: str
    hora: datetime

class AuditorTrading:
    def __init__(self, db_path: str = 'anima_trading.db') -> None:
        self.db_path = db_path
        self._crear_tabla()

    @contextmanager
    def _conexion(self) -> Any:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _crear_tabla(self) -> None:
        with self._conexion() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ordenes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    activo TEXT NOT NULL,
                    resultado TEXT NOT NULL,
                    hora TEXT NOT NULL
                )
            ''')
            conn.commit()

    def registrar_orden(self, orden: Orden) -> None:
        with self._conexion() as conn:
            conn.execute(
                'INSERT INTO ordenes (tipo, activo, resultado, hora) VALUES (?, ?, ?, ?)',
                (orden.tipo, orden.activo, orden.resultado, orden.hora.isoformat())
            )
            conn.commit()
        logging.info(f"Orden registrada: {orden}")
