# gaba.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    GABA: detecta velas de reversión (martillo o doji) y opera en la dirección esperada de reversión.

    - Martillo (hammer): cuerpo pequeño y sombra inferior al menos 2x el cuerpo.
    - Doji: cuerpo muy pequeño (body/rango <= 0.1).

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'].
        params: {
            'body_threshold': float (proporción máxima de cuerpo sobre rango para doji, por defecto 0.1),
            'wick_multiplier': float (múltiplo mínimo de sombra inferior sobre cuerpo para hammer, por defecto 2),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'gaba') o None si no se detecta patrón.
    """
    # Parámetros
    body_th = params.get('body_threshold', 0.1)
    wick_mul = params.get('wick_multiplier', 2)
    pair = params.get('pair', '')

    # Requiere al menos 1 vela para evaluar
    if df.empty:
        return None
    
    # Última vela
    last = df.iloc[-1]
    open_p, high_p, low_p, close_p = last['open'], last['high'], last['low'], last['close']
    body = abs(close_p - open_p)
    total_range = high_p - low_p

    # Evitar división por cero
    if total_range == 0:
        return None

    lower_wick = min(open_p, close_p) - low_p
    upper_wick = high_p - max(open_p, close_p)

    # Detectar doji: cuerpo pequeño en comparación al rango
    is_doji = (body / total_range) <= body_th
    # Detectar hammer bullish: sombra inferior grande y cuerpo pequeño
    is_hammer = (lower_wick >= wick_mul * body)
    # Detectar hanging man (inverted hammer) con sombra superior grande
    is_inverted = (upper_wick >= wick_mul * body)

    if is_doji:
        # Reversión: opuesto del color de la vela previa
        prev = df.iloc[-2] if len(df) >= 2 else None
        if prev is not None:
            if prev['close'] > prev['open']:
                direction = 'PUT'
            else:
                direction = 'CALL'
        else:
            return None
    elif is_hammer:
        # Hammer bullish: señal CALL
        direction = 'CALL'
    elif is_inverted:
        # Inverted hammer: señal PUT
        direction = 'PUT'
    else:
        return None

    return Signal(pair=pair, direction=direction, strategy='gaba')