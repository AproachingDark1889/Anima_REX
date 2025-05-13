# turno_over.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    TURNO_OVER: opera cuando la última vela cambió de color respecto a la anterior.
    - Si la vela actual es alcista y la anterior bajista → CALL
    - Si la vela actual es bajista y la anterior alcista → PUT
    En cualquier otro caso no genera señal.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'pair': str (símbolo del par, inyectado desde config)
        }

    Returns:
        Signal(pair, direction, 'turno_over') o None si no hay alternancia.
    """
    pair = params.get('pair', '')

    # Necesitamos al menos 2 velas para comparar
    if len(df) < 2:
        return None

    # Tomar las últimas 2 velas
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    # Determinar colores
    prev_bull = curr_close = False
    prev_bull = prev['close'] > prev['open']
    curr_bull = curr['close'] > curr['open']

    # Si hubo alternancia de color
    if curr_bull and not prev_bull:
        direction = 'CALL'
    elif not curr_bull and prev_bull:
        direction = 'PUT'
    else:
        return None

    return Signal(pair=pair, direction=direction, strategy='turno_over')