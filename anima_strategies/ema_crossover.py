# anima_strategies/ema_crossover.py
import pandas as pd
from signal_model import Signal

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    Genera una señal cuando la EMA rápida cruza sobre la EMA lenta.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: Diccionario con claves:
            - fast_period: período de la EMA rápida (int).
            - slow_period: período de la EMA lenta (int).
            - pair (opcional): par a incluir en la señal.

    Returns:
        Signal(pair, direction, strategy) si detecta cruce, o None en caso contrario.
    """
    fast = params.get('fast_period', 9)
    slow = params.get('slow_period', 21)

    # No hay suficiente histórico para calcular ambas EMAs
    if len(df) < slow:
        return None

    # Calculamos las EMAs
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

    # Detectar cruce alcista en la última barra
    if ema_fast.iloc[-2] <= ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1]:
        return Signal(
            pair=params.get('pair', df.name),
            direction='CALL',
            strategy='ema_crossover'
        )

    # Detectar cruce bajista en la última barra
    if ema_fast.iloc[-2] >= ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1]:
        return Signal(
            pair=params.get('pair', df.name),
            direction='PUT',
            strategy='ema_crossover'
        )

    # Sin señal
    return None
