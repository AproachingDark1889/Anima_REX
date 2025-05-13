"""
Módulo: anima_data.py (Versión 3.3 Simbiótica Absoluta)
Objetivo: Ingesta multipar paralela con validación profunda, trazabilidad total, resiliencia completa y docstrings quirúrgicos.
"""

import os
import time
import traceback
import logging
import pandas as pd
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.anima_broker import AnimaBroker
from anima_config import cargar_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d"]
DEFAULT_TIMEFRAME = "1m"
DEFAULT_MINUTES = 60
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # segundos
MAX_WORKERS = 4

class AnimaData:
    """
    Gestor de almacenamiento de datos OHLCV: SQLite y Parquet.
    """
    def __init__(self, broker: AnimaBroker, data_dir: str = "data", db_path: str = "ohlcv.sqlite"):
        os.makedirs(data_dir, exist_ok=True)
        self.broker = broker
        self.data_dir = data_dir
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ohlcv (
                    symbol TEXT,
                    timeframe TEXT,
                    timestamp INTEGER,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY(symbol, timeframe, timestamp)
                )
            """)

    def store_data(self, df: pd.DataFrame, symbol: str, timeframe: str, parquet: bool, sqlite_store: bool):
        """
        Guarda el DataFrame en Parquet y SQLite, si se habilita.
        """
        if df.empty:
            logger.warning(f"[{symbol}] DataFrame vacío. Nada que guardar.")
            return

        if df.isnull().values.any():
            logger.warning(f"[{symbol}] Valores nulos detectados en los datos descargados.")

        if parquet:
            parquet_path = os.path.join(self.data_dir, f"{symbol}_{timeframe}.parquet")
            df.to_parquet(parquet_path, index=False)

        if sqlite_store:
            with sqlite3.connect(self.db_path) as conn:
                try:
                    conn.executemany("""
                        INSERT OR REPLACE INTO ohlcv
                        (symbol, timeframe, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, [tuple(row) for _, row in df.iterrows()])
                except Exception as e:
                    logger.error(f"[{symbol}] Error en inserción SQLite: {e}")

    def fetch_and_persist_ohlcv(self, symbol: str, timeframe: str, since: int, until: int = None, parquet: bool = True, sqlite_store: bool = True):
        """
        Descarga datos OHLCV del broker, valida, convierte y guarda. Incluye reintentos.
        """
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                ohlcv = self.broker.fetch_ohlcv(symbol, timeframe, since, until)

                if not isinstance(ohlcv, list) or not all(isinstance(row, list) and len(row) == 6 for row in ohlcv):
                    raise ValueError(f"[{symbol}] Datos OHLCV malformados o corruptos.")

                df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["symbol"] = symbol
                df["timeframe"] = timeframe
                df = df[["symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]]

                self.store_data(df, symbol, timeframe, parquet, sqlite_store)
                return len(df)

            except Exception:
                attempt += 1
                logger.error(f"[{symbol}] Error en intento {attempt} de {MAX_RETRIES}:")
                logger.error(traceback.format_exc())
                time.sleep(RETRY_BACKOFF * attempt)
        return 0

def load_ingestion_config():
    cfg = cargar_config()
    pairs = cfg.get("pairs", [])
    timeframe = cfg.get("timeframe", DEFAULT_TIMEFRAME)
    minutos = cfg.get("duracion", DEFAULT_MINUTES)

    if not isinstance(pairs, list) or not pairs:
        raise ValueError("'pairs' debe ser una lista no vacía en config.yml")
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError(f"Timeframe '{timeframe}' no soportado. Soportados: {SUPPORTED_TIMEFRAMES}")
    if not isinstance(minutos, int) or minutos <= 0:
        raise ValueError("'duracion' debe ser un entero positivo")

    return pairs, timeframe, minutos

def get_time_range(minutos):
    now = int(time.time())
    return now - (minutos * 60), now

def run_ohlcv_ingestion(symbol, timeframe, since, until, data_manager, parquet, sqlite_store):
    start = time.time()
    registros = data_manager.fetch_and_persist_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        since=since,
        until=until,
        parquet=parquet,
        sqlite_store=sqlite_store
    )
    elapsed = round(time.time() - start, 2)
    logger.info(f"[OHLCV] {symbol} → {registros} registros guardados en {elapsed}s")

def fetch_and_store_ohlcv(
    parquet: bool = True,
    sqlite_store: bool = True,
    broker: AnimaBroker = None,
    data_manager: AnimaData = None
):
    """
    Ingesta multipar paralela y validada de datos OHLCV.
    Incluye validaciones iniciales, reintentos, trazabilidad y ejecución simbiótica total.
    """
    try:
        pairs, timeframe, minutos = load_ingestion_config()
        since, until = get_time_range(minutos)

        if broker is None:
            broker = AnimaBroker()
        if data_manager is None:
            data_manager = AnimaData(broker)

        start_total = time.time()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(
                    run_ohlcv_ingestion,
                    symbol,
                    timeframe,
                    since,
                    until,
                    data_manager,
                    parquet,
                    sqlite_store
                ) for symbol in pairs
            ]
            for future in as_completed(futures):
                pass

        total_time = round(time.time() - start_total, 2)
        logger.info(f"[OHLCV] ✅ Ingesta completada en {total_time}s para {len(pairs)} pares.")

    except Exception:
        logger.error("[fetch_and_store_ohlcv] ✖ Error crítico en ingesta multipar:")
        logger.error(traceback.format_exc())
