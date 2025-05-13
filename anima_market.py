# anima_market.py
# Módulo de mercado: obtiene datos históricos de OHLCV

import time
import json
import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from anima_config import cargar_config
from core.anima_broker import AnimaBroker, conectar_broker  # Importar la función conectar_broker necesaria
from anima_utils import parse_timeframe

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MarketError(Exception):
    pass

def get_historical_ohlcv(symbol: str, timeframe: str, start: int = None, end: int = None, limit: int = None) -> pd.DataFrame:
    """
    Obtiene datos históricos OHLCV desde el broker, los convierte en un DataFrame
    y filtra los datos por timestamp <= end.

    Args:
        symbol (str): El símbolo del mercado (por ejemplo, 'BTC/USD').
        timeframe (str): El marco temporal (por ejemplo, '1h', '1d').
        start (int): Timestamp inicial (en segundos).
        end (int): Timestamp final (en segundos).

    Returns:
        pd.DataFrame: Un DataFrame con los datos OHLCV filtrados.
    """
    # Cargar configuración y credenciales
    cfg = cargar_config()
    cred = cfg.get("credenciales", {})

    # Conectar al broker con las credenciales
    broker = conectar_broker(cred)
    # Si se solicita un número fijo de velas, calcular rango automático
    if limit is not None:
        tf_seconds = parse_timeframe(timeframe)
        end_ts = int(time.time())
        since_ts = end_ts - limit * tf_seconds
        data = broker.fetch_ohlcv(symbol, timeframe, since_ts, end_ts)
        df = pd.DataFrame(data, columns=["timestamp","open","high","low","close","volume"])
        return df

    # Obtener datos OHLCV desde el broker
    if end:
        ohlcv_data = broker.fetch_ohlcv(symbol, timeframe, start)
        # Filtrar por 'end' usando Pandas
        ohlcv_df = pd.DataFrame(ohlcv_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        ohlcv_df = ohlcv_df[ohlcv_df["timestamp"] <= end]
        ohlcv_data = ohlcv_df.values.tolist()
    else:
        ohlcv_data = broker.fetch_ohlcv(symbol, timeframe, start)

    # Convertir los datos a un DataFrame
    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    return df

def get_latest_price(symbol: str) -> float:
    """
    Devuelve el precio bid/ask promedio actual.
    """
    from anima_rex.anima_broker import conectar_broker

    broker = conectar_broker()
    bid, ask = broker.fetch_bid_ask(symbol)
    return (bid + ask) / 2

def parse_timeframe(tf: str) -> int:
    """
    Convierte un timeframe tipo '1m', '1h', '1d' en segundos.
    """
    unit = tf[-1]
    amount = int(tf[:-1])
    if unit == 'm':
        return amount * 60
    elif unit == 'h':
        return amount * 3600
    elif unit == 'd':
        return amount * 86400
    else:
        raise ValueError(f"Timeframe inválido: {tf}")

# Función de ejemplo que podría no usarse
def unused_helper():
    print("Este helper no se usa en ningún lado")
