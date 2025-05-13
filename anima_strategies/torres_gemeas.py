# torres_gemeas.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    TORRES_GÊMEAS: detecta dos velas consecutivas idénticas (mismo open y close) 
    y genera señal en la tercera vela en la misma dirección de las gemelas.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número mínimo de velas, mínimo 3),
            'pair': str (símbolo del par, inyectado desde config)
        }

    Returns:
        Signal(pair, direction, 'torres_gemeas') o None si no detecta patrón.
    """
    pair = params.get('pair', '')
    # Necesitamos al menos 3 velas
    if len(df) < 3:
        return None

    # Vela gemela 1 y 2
    bar1 = df.iloc[-3]
    bar2 = df.iloc[-2]
    bar3 = df.iloc[-1]

    # Revisar si open y close idénticos
    if bar1['open'] == bar2['open'] and bar1['close'] == bar2['close']:
        # Determinar dirección de las gemelas
        if bar2['close'] > bar2['open']:
            direction = 'CALL'
        elif bar2['close'] < bar2['open']:
            direction = 'PUT'
        else:
            return None
        # Retornar señal para la tercera vela
        return Signal(pair=pair, direction=direction, strategy='torres_gemeas')

    return None
