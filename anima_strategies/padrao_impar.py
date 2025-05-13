    # padrao_impar.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    PADRÃO_IMPAR: analiza las últimas N velas (por defecto 5) y, si la cantidad de velas alcistas o bajistas
    es impar, abre posición contraria (odd bulls->PUT, odd bears->CALL).

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número de velas a contar, por defecto 5),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'padrao_impar') o None si no hay condición impar.
    """
    window = int(params.get('window', 5))
    if len(df) < window:
        return None
    recent = df.iloc[-window:]
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()
    if bulls % 2 != 0:
        direction = 'PUT'
    elif bears % 2 != 0:
        direction = 'CALL'
    else:
        return None
    pair = params.get('pair', '')
    return Signal(pair=pair, direction=direction, strategy='padrao_impar')