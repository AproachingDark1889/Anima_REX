# seven_flip.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    SEVEN_FLIP: detecta una serie de 7 velas del mismo color en la ventana y opera contrarian en la siguiente.

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (tamaño de la serie, por defecto 7),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'seven_flip') si las últimas 7 velas son todas verdes o todas rojas; None en otro caso.
    """
    window = params.get('window', 7)
    pair = params.get('pair', '')

    # Si no hay suficientes velas, no hay señal
    if len(df) < window:
        return None

    recent = df.iloc[-window:]
    # Contar velas alcistas y bajistas
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()

    # Si todas son alcistas, invertir -> PUT
    if bulls == window:
        direction = 'PUT'
    # Si todas son bajistas, invertir -> CALL
    elif bears == window:
        direction = 'CALL'
    else:
        return None

    return Signal(pair=pair, direction=direction, strategy='seven_flip')
