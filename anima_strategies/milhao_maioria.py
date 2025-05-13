# milhao_maioria.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    MILHÃO_MAIORIA: analiza las últimas N velas (por defecto 10) y, si la mayoría (threshold por defecto N//2+1)
    son alcistas, devuelve CALL; si la mayoría son bajistas, devuelve PUT.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número de velas a contar, por defecto 10),
            'threshold': int (mayoría mínima, por defecto window//2+1),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'milhao_maioria') o None si no hay mayoría clara.
    """
    window = params.get('window', 10)
    threshold = params.get('threshold', window//2 + 1)
    pair = params.get('pair', '')

    # Verificar suficientes datos
    if len(df) < window:
        return None

    recent = df.iloc[-window:]
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()

    # Determinar señal según majority
    if bulls >= threshold:
        direction = 'CALL'
    elif bears >= threshold:
        direction = 'PUT'
    else:
        return None

    return Signal(pair=pair, direction=direction, strategy='milhao_maioria')
