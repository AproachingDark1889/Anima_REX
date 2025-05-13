# mhi2_minoria.py
from signal_model import Signal
import pandas as pd


    
def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    MHI2_MINORIA: Variante contraria de MHI2_MAIORIA.
    Analiza las últimas N velas (por defecto 5) y, si la mayoría de esas velas son alcistas (>= threshold), devuelve PUT;
    si la mayoría de esas velas son bajistas (>= threshold), devuelve CALL.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número de velas a contar, por defecto 5),
            'threshold': int (mayoría mínima, por defecto window//2+1),
            'pair': str (símbolo del par, inyectado desde config)
        }

    Returns:
        Signal(pair, direction, 'mhi2_minoria') o None si no se alcanza threshold.
    """
    window = int(params.get('window', 5))
    threshold = int(params.get('threshold', window//2 + 1))
    if len(df) < window:
        return None
    recent = df.iloc[-window:]
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()
    if bulls >= threshold:
        direction = 'PUT'
    elif bears >= threshold:
        direction = 'CALL'
    else:
        return None
    pair = params.get('pair', '')
    return Signal(pair=pair, direction=direction, strategy='mhi2_minoria')