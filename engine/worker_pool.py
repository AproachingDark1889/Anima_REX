# File: worker_pool.py (con cambios)
import threading
import time
import logging
from anima_config import cargar_config
from anima_db import DBHandler
from anima_strategies.factory import estrategia_factory
from engine.signal_bus import SignalBus

logger = logging.getLogger(__name__)

# Map timeframes to seconds
_tf_seconds = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
}

market_lock = threading.Lock()

class StrategyWorker(threading.Thread):
    def __init__(self, pair: str, estrategia_cfg: dict, bus: SignalBus, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.pair = pair
        self.estrategia_cfg = estrategia_cfg
        self.bus = bus
        self.stop_event = stop_event
        self.interval = estrategia_cfg.get('interval', 60)
        self.error_threshold = estrategia_cfg.get('error_threshold', 5)
        self.pause_duration = estrategia_cfg.get('pause_duration', 300)
        self.strategy_fn = estrategia_factory(estrategia_cfg)
        self.error_count = 0

    def run(self):
        nombre = self.estrategia_cfg['nombre']
        logger.info(f"[{nombre}] Iniciando análisis en {self.pair}, cada {self.interval}s")
        while not self.stop_event.is_set():
            try:
                with market_lock:
                    # Carga histórico desde BD en lugar de usar 'since' o 'limit'
                    df_full = DBHandler().load_ohlcv(
                        self.pair,
                        self.estrategia_cfg.get('timeframe', '1m')
                    )
                    # Aplicar ventana de datos
                    window = self.estrategia_cfg['params'].get('window', self.estrategia_cfg.get('limit', 100))
                    df = df_full.iloc[-window:]
                if df is None or df.empty:
                    self.error_count = 0
                    time.sleep(self.interval)
                    continue
                else:
                    try:
                        senal = self.strategy_fn(df)
                    except ConnectionError as e:
                        logger.warning(f"[{nombre}] Conexión perdida: {e}. Reintentando...")
                        self.error_count += 1
                        if self.error_count >= self.error_threshold:
                            logger.warning(f"[{nombre}] {self.error_count} errores consecutivos, pausando {self.pause_duration}s")
                            time.sleep(self.pause_duration)
                            self.error_count = 0
                        continue
                    except Exception as e:
                        logger.error(f"[{nombre}] Error al generar señal: {e}")
                        continue

                    if senal is None:
                        continue

                    try:
                        senal.strategy = nombre
                        self.bus.publish(senal)
                        self.error_count = 0
                    except Exception as e:
                        logger.error(f"[{nombre}] Error al publicar señal: {e}")

            except Exception as e:
                msg = str(e).lower()
                logger.error(f"[{nombre}] Error en bucle de worker: {e}")
                if any(x in msg for x in ('socket', 'websocket', 'connection')):
                    self.error_count += 1
                    if self.error_count >= self.error_threshold:
                        logger.warning(f"[{nombre}] {self.error_count} errores consecutivos en bucle, pausando {self.pause_duration}s")
                        time.sleep(self.pause_duration)
                        self.error_count = 0
            time.sleep(self.interval)