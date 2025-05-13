# mhi3_minoria.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    MHI3_MINORIA: Variante contraria de MHI3_MAIORIA.
    Analiza las últimas N velas (por defecto 8) y, si la mayoría (threshold por defecto N//2+1)
    son alcistas (>= threshold), devuelve PUT; si la mayoría son bajistas (>= threshold), devuelve CALL.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int, por defecto 8,
            'threshold': int, por defecto window//2+1,
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'mhi3_minoria') o None si no se alcanza threshold.
    """
    window = params.get('window', 8)
    threshold = params.get('threshold', window//2 + 1)
    pair = params.get('pair', '')

    if len(df) < window:
        return None

    recent = df.iloc[-window:]
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()

    # Contrarian a la mayoría
    if bulls >= threshold:
        direction = 'PUT'
    elif bears >= threshold:
        direction = 'CALL'
    else:
        return None

    return Signal(pair=pair, direction=direction, strategy='mhi3_minoria')
