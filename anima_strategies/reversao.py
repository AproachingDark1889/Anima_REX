# anima_strategies/reversao.py

from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    REVERSÃO: detecta reversión tras una vela con gap o cuerpo grande.
    
    - Gap al alza: open_curr > prev_close * (1 + gap_threshold)  → PUT
    - Gap a la baja: open_curr < prev_close * (1 - gap_threshold) → CALL
    - Cuerpo grande: body_prev > body_threshold * range_prev
      → si vela previa fue bullish, PUT; si fue bearish, CALL

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'gap_threshold': float, proporción mínima de gap (p.ej. 0.001),
            'body_threshold': float, fracción mínima de cuerpo respecto al rango (p.ej. 0.8),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'reversao') o None si no detecta patrón.
    """
    if len(df) < 2:
        return None

    # Parámetros
    gap_th  = params.get('gap_threshold', 0.001)
    body_th = params.get('body_threshold', 0.8)
    pair    = params.get('pair', '')

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    prev_open, prev_close = prev['open'], prev['close']
    curr_open = curr['open']

    # Detectar gap
    if curr_open > prev_close * (1 + gap_th):
        # Gap al alza, reversión a la baja
        return Signal(pair=pair, direction='PUT', strategy='reversao')
    if curr_open < prev_close * (1 - gap_th):
        # Gap a la baja, reversión al alza
        return Signal(pair=pair, direction='CALL', strategy='reversao')

    # Detectar cuerpo grande de la vela previa
    prev_high, prev_low = prev['high'], prev['low']
    body_prev = abs(prev_close - prev_open)
    range_prev = prev_high - prev_low
    if range_prev <= 0:
        return None
    if body_prev >= body_th * range_prev:
        # Vela previa fuerte; señal contraria a su dirección
        if prev_close > prev_open:
            return Signal(pair=pair, direction='PUT', strategy='reversao')
        else:
            return Signal(pair=pair, direction='CALL', strategy='reversao')

    return None
