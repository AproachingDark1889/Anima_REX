
# mhi3_maioria.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    MHI3_MAIORIA: analiza las últimas N velas (por defecto 8) y, si la mayoría (threshold por defecto N//2+1)
    son alcistas, devuelve señal CALL; si la mayoría son bajistas, devuelve PUT.
    Versión extendida de ventana de conteo.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número de velas a contar, por defecto 8),
            'threshold': int (mayoría mínima, por defecto window//2+1),
            'pair': str (símbolo del par, inyectado desde config)
        }

    Returns:
        Signal(pair, direction, 'mhi3_maioria') o None si no hay mayoría clara.
    """
    window = int(params.get('window', 8))
    threshold = int(params.get('threshold', window//2 + 1))
    if len(df) < window:
        return None
    recent = df.iloc[-window:]
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()
    if bulls >= threshold:
        direction = 'CALL'
    elif bears >= threshold:
        direction = 'PUT'
    else:
        return None
    pair = params.get('pair', '')
    return Signal(pair=pair, direction=direction, strategy='mhi3_maioria')

    
