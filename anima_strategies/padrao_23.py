# padrao_23.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    PADRÃO_23: analiza un patrón fijo de 5 velas:
      - [GREEN, GREEN, RED, RED, RED] → PUT
      - [RED, RED, GREEN, GREEN, GREEN] → CALL
    Cualquier otro patrón no genera señal.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número de velas a analizar, por defecto 5),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'padrao_23') o None si no coincide patrón.
    """
    window = int(params.get('window', 5))
    if len(df) < window:
        return None
    recent = df.iloc[-window:]
    colors = [(recent['close'].iloc[i] > recent['open'].iloc[i]) for i in range(-window, 0)]
    if colors == [True, True, False, False, False]:
        direction = 'PUT'
    elif colors == [False, False, True, True, True]:
        direction = 'CALL'
    else:
        return None
    pair = params.get('pair', '')
    return Signal(pair=pair, direction=direction, strategy='padrao_23')
