import time, traceback
from anima_logger import setup_logger
logger = setup_logger("data_utils")
from core.anima_broker import conectar_broker
from anima_data import AnimaData
from anima_config import cargar_config
from threading import Event
from observability import ohlcv_ingestion_latency, error_counter  # new imports

def fetch_and_persist_ohlcv(
    symbol: str = None,
    timeframe: str = None,
    minutos: int = None,
    parquet: bool = True,
    sqlite_store: bool = True,
    stop_event=None
):
    """
    Descarga y almacena datos OHLCV usando AnimaData.

    Parámetros:
    ----------
    symbol : str
        Par de divisas (ej. "EURUSD"). Si es None, se lee de config.yml.
    timeframe : str
        Marco temporal (ej. "1m"). Si es None, se lee de config.yml.
    minutos : int
        Cuántos minutos atrás descargar. Si es None, se lee de config.yml.
    parquet : bool
        Si True, guarda en formato Parquet.
    sqlite_store : bool
        Si True, guarda en SQLite.
    stop_event : threading.Event
        Evento para controlar la detención de la descarga.
    """
    try:
        # Medir latencia de ingesta OHLCV
        with ohlcv_ingestion_latency.time():
            cfg = cargar_config()
            symbol    = symbol    or cfg.get("mercado", {}).get("par",       "EURUSD")
            timeframe = timeframe or cfg.get("mercado", {}).get("timeframe", "1m")
            minutos   = minutos   or cfg.get("mercado", {}).get("minutos",   60)

            # Asegurar un stop_event válido
            if stop_event is None:
                stop_event = Event()
            # Conectar broker
            broker = conectar_broker(cfg.get("credenciales", {}), stop_event)
            data_manager = AnimaData(broker)

            logger.info(f"[OHLCV] Descargando {symbol} {timeframe} ({minutos} min)")
            since = int(time.time()) - minutos * 60
            until = int(time.time())
            data_manager.fetch_and_store(
                symbol=symbol,
                timeframe=timeframe,
                since=since,
                until=until,
                parquet=parquet,
                sqlite_store=sqlite_store
            )
            logger.info(f"[OHLCV] Completado para {symbol} {timeframe}")
    except Exception:
        # Contar error en componente 'ohlcv_ingestion'
        error_counter.labels(component='ohlcv_ingestion').inc()
        logger.exception("Error en fetch_and_persist_ohlcv")
