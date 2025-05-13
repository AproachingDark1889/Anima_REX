# melhor_de_3.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    MELHOR_DE_3: toma las últimas N velas (por defecto 3) y opera según la más frecuente:
      - 2 o más velas alcistas  => CALL
      - 2 o más velas bajistas => PUT
      - empate => None

    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (tamaño de la ventana, por defecto 3),
            'pair': str (símbolo del par)
        }

    Returns:
        Signal(pair, direction, 'melhor_de_3') o None si no hay mayoría.
    """
    window = int(params.get('window', 3))
    pair = params.get('pair', '')

    # Verificar suficientes datos
    if len(df) < window:
        return None

    recent = df.iloc[-window:]
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()

    if bulls > bears:
        direction = 'CALL'
    elif bears > bulls:
        direction = 'PUT'
    else:
        return None

    return Signal(pair=pair, direction=direction, strategy='melhor_de_3')
