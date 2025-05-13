# File: anima_supervisor.py
import logging
import sqlite3
from collections import deque
from typing import Deque

from anima_db import DBHandler

logger = logging.getLogger(__name__)

class SupervisorMetaCognitivo:
    """
    Supervisa el win-rate sobre una ventana móvil, ajusta niveles
    de martingala hacia arriba y hacia abajo, y persiste su estado.
    """

    DB_TABLE = "supervisor_state"

    def __init__(self, config):
        # Configuración
        sup_cfg = config.get("supervisor", {})
        self.window_size = sup_cfg.get("window_size", 20)
        self.min_win_rate = sup_cfg.get("min_win_rate", 0.6)
        self.martingala_levels = config["martingala"]["niveles"]
        # Estado en memoria
        self.trades: Deque[str] = deque(maxlen=self.window_size)
        self.current_level_idx = 0
        # Carga estado persistido (si existe)
        self._load_state()

    def _db(self):
        return sqlite3.connect(DBHandler().db_path)

    def _init_table(self):
        with self._db() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.DB_TABLE} (
                    key TEXT PRIMARY KEY,
                    value INTEGER
                )
            """)
            conn.commit()

    def _load_state(self):
        self._init_table()
        with self._db() as conn:
            cur = conn.execute(f"SELECT value FROM {self.DB_TABLE} WHERE key='level_idx'")
            row = cur.fetchone()
            if row:
                idx = row[0]
                if 0 <= idx < len(self.martingala_levels):
                    self.current_level_idx = idx
                    logger.info(f"[Supervisor] Nivel restaurado: {self.current_level_idx}")
            # No cargamos trades; empezamos ventana vacía

    def _persist_level(self):
        with self._db() as conn:
            conn.execute(f"""
                INSERT INTO {self.DB_TABLE}(key,value)
                VALUES('level_idx',?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (self.current_level_idx,))
            conn.commit()

    def register_trade(self, result: str):
        """
        Registra 'WIN' o 'LOSS', evalúa performance y ajusta martingala.
        """
        # Asegurar índice dentro de límites antes de procesar
        self.current_level_idx = max(0, min(self.current_level_idx, len(self.martingala_levels)-1))
        if result not in ("WIN", "LOSS"):
            logger.warning(f"[Supervisor] Resultado inválido: {result}")
            return
        # Dinámica de martingala: sube nivel tras pérdida, reset tras ganancia
        max_idx = len(self.martingala_levels) - 1
        if result == "LOSS":
            if self.current_level_idx < max_idx:
                self.current_level_idx += 1
                logger.warning(f"[Supervisor] Pérdida detectada. Nivel martingala incrementado a idx={self.current_level_idx}")
                self._persist_level()
            else:
                logger.warning("[Supervisor] Nivel martingala ya en tope; no se incrementa más.")
        else:  # WIN
            if self.current_level_idx != 0:
                self.current_level_idx = 0
                logger.info(f"[Supervisor] Ganancia detectada. Nivel martingala reiniciado a idx=0")
                self._persist_level()
        # Añadir resultado a ventana móvil para monitorización de win-rate
        self.trades.append(result)
        # Evaluar performance usando ventana móvil si está completa
        if len(self.trades) == self.window_size:
            self._evaluate_performance()

    def _evaluate_performance(self):
        wins = sum(1 for r in self.trades if r == "WIN")
        win_rate = wins / self.window_size
        # Registrar evaluación de win-rate para monitoring
        logger.info(f"[Supervisor] Win rate última ventana: {win_rate:.2%}")
        # Límite máximo de niveles de martingala
        max_idx = len(self.martingala_levels) - 1

        if win_rate < self.min_win_rate:
            if self.current_level_idx < max_idx:
                self.current_level_idx += 1
                logger.warning(f"[Supervisor] Bajo umbral ({win_rate:.2%} < {self.min_win_rate:.2%}). Subiendo nivel a idx={self.current_level_idx}")
                self._persist_level()
            else:
                logger.warning("[Supervisor] Nivel martingala ya en tope tras evaluación; no se incrementa.")

        elif win_rate >= self.min_win_rate and self.current_level_idx > 0:
            self.current_level_idx -= 1
            logger.info(f"[Supervisor] Rendimiento recuperado ({win_rate:.2%} ≥ {self.min_win_rate:.2%}). Bajando nivel a idx={self.current_level_idx}")
            self._persist_level()

    def get_current_monto(self) -> float:
        """
        Devuelve el stake actual según el nivel de martingala.
        """
        # Asegurar índice dentro de rango válido
        idx = max(0, min(self.current_level_idx, len(self.martingala_levels)-1))
        return self.martingala_levels[idx]
