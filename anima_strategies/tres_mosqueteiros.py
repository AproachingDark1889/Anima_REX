# tres_mosqueteiros.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    TRÊS_MOSQUETEIROS: detecta el patrón Three White Soldiers o Three Black Crows en las últimas 3 velas.
    - Tres White Soldiers: tres velas consecutivas alcistas, cada apertura y cierre mayores que la vela anterior → CALL
    - Three Black Crows: tres velas consecutivas bajistas, cada apertura y cierre menores que la vela anterior → PUT

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'pair': str (símbolo del par, inyectado desde config)
        }

    Returns:
        Signal(pair, direction, 'tres_mosqueteiros') o None si no detecta patrón.
    """
    pair = params.get('pair', '')
    # Se requieren al menos 3 velas
    if len(df) < 3:
        return None

    # Últimas tres velas
    a, b, c = df.iloc[-3], df.iloc[-2], df.iloc[-1]

    # Funciones auxiliares
    def is_bull(bar): return bar['close'] > bar['open']
    def is_bear(bar): return bar['close'] < bar['open']

    # Three White Soldiers
    if (is_bull(a) and is_bull(b) and is_bull(c)
        and b['open'] > a['open'] and c['open'] > b['open']
        and b['close'] > a['close'] and c['close'] > b['close']):
        return Signal(pair=pair, direction='CALL', strategy='tres_mosqueteiros')

    # Three Black Crows
    if (is_bear(a) and is_bear(b) and is_bear(c)
        and b['open'] < a['open'] and c['open'] < b['open']
        and b['close'] < a['close'] and c['close'] < b['close']):
        return Signal(pair=pair, direction='PUT', strategy='tres_mosqueteiros')

    return None