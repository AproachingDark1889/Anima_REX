# tres_vizinhos.py
from signal_model import Signal
import pandas as pd
from anima_market import get_historical_ohlcv

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    TRÊS_VIZINHOS: utiliza tres pares vecinos. Si 2 de 3 pares suben, entra CALL en el tercero;
    si 2 de 3 pares bajan, entra PUT en el tercero.

    Args:
        df: DataFrame (no utilizado directamente en esta estrategia).
        params: {
            'peers': list[str] de tres símbolos (p.ej. ['USDJPY-OTC','EURUSD-OTC','GBPUSD-OTC']),
            'timeframe': str (intervalo de velas, p.ej. '1m'),
            'pair': str (se ignora, estrategia determina el par objetivo)
        }

    Returns:
        Signal para el par objetivo con direction 'CALL' o 'PUT', o None si no hay mayoría.
    """
    peers = params.get('peers', [])
    tf = params.get('timeframe', '1m')
    if len(peers) != 3:
        return None

    movements = {}
    # Analizar cada par: sube o baja en la última vela
    for p in peers:
        df_p = get_historical_ohlcv(p, timeframe=tf, limit=2)
        if df_p is None or len(df_p) < 2:
            return None
        prev, last = df_p.iloc[-2], df_p.iloc[-1]
        movements[p] = 'up' if last['close'] > prev['close'] else 'down'

    ups = [p for p, m in movements.items() if m == 'up']
    downs = [p for p, m in movements.items() if m == 'down']

    # 2 ups -> CALL on the down; 2 downs -> PUT on the up
    if len(ups) == 2 and len(downs) == 1:
        target = downs[0]
        direction = 'CALL'
    elif len(downs) == 2 and len(ups) == 1:
        target = ups[0]
        direction = 'PUT'
    else:
        return None

    return Signal(pair=target, direction=direction, strategy='tres_vizinhos')