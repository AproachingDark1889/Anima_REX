# anima_signals_download.py
"""
Módulo de señales: obtiene datos de mercado reales y genera señales usando estrategias.
"""
from datetime import datetime
from anima_config import cargar_config
from anima_market import get_historical_ohlcv
from signal_model import Signal  # ← Usa esta en lugar de importar Signal desde factory

class Signal:
    """
    Representa una señal de trading.
    """
    def __init__(self, pair: str, direction: str, strategy: str, timestamp: str = None):
        self.pair = pair.upper()
        self.direction = direction.upper()  # CALL o PUT
        self.strategy = strategy
        self.timestamp = timestamp or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    def __repr__(self):
        return f"<Signal {self.timestamp} | {self.pair} | {self.direction} | {self.strategy}>"


def obtener_senal() -> Signal | None:
    """
    Genera una señal basada en datos reales del mercado y la estrategia configurada.

    Pasos:
      1) Carga configuración (par, timeframe, limit, estrategia).
      2) Descarga datos históricos OHLCV.
      3) Obtiene la función de estrategia.
      4) Devuelve una instancia de Signal o None.
    """
    # 1) Cargar configuración
    config = cargar_config()
    pair = config.get("par")
    timeframe = config.get("timeframe", "1m")
    limit = config.get("limit", 100)

    # 2) Descargar datos históricos reales
    df = get_historical_ohlcv(pair=pair, timeframe=timeframe, limit=limit)

    # 3) Obtener función de estrategia (con inyección de 'pair')
    estrategia_cfg = config.get("estrategia", {})
    # Inyectar el par desde config en los parámetros de la estrategia
    params = estrategia_cfg.get("params", {})
    params['pair'] = pair
    estrategia_cfg['params'] = params
    estrategia_fn = estrategia_factory(estrategia_cfg)

    # 4) Generar señal
    senal = estrategia_fn(df, estrategia_cfg.get("params", {}))
    if senal:
        # Actualizar timestamp a UTC actual
        senal.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    return senal
