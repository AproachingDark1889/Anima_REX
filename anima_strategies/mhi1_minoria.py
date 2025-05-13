
# mhi1_minoria.py
from signal_model import Signal
import pandas as pd

def generate_signal(df: pd.DataFrame, params: dict) -> Signal | None:
    """
    MHI1_MINORIA: analiza las últimas N velas (por defecto 3) y, si la mayoría son bajistas,
    devuelve señal CALL para la siguiente vela; si la mayoría son alcistas, devuelve PUT.
    Contrario a MHI1_MAIORIA.
    
    Args:
        df: DataFrame con columnas ['open','high','low','close','volume'] y datetime index.
        params: {
            'window': int (número de velas a contar, por defecto 3),
            'pair': str (símbolo del par, inyectado desde config)
        }
        
    Returns:
        Signal(pair, direction, 'mhi1_minoria') o None si no hay mayoría clara.
    """
    window = params.get('window', 3)
    pair = params.get('pair', '')
    
    # No hay suficientes velas para analizar
    if len(df) < window:
        return None
    
    # Extraer las últimas `window` velas
    recent = df.iloc[-window:]
    
    # Contar velas alcistas (bulls) y bajistas (bears)
    bulls = (recent['close'] > recent['open']).sum()
    bears = (recent['close'] < recent['open']).sum()
    
    # Determinar señal según minoría invertida
    if bears > bulls:
        direction = 'CALL'
    elif bulls > bears:
        direction = 'PUT'
    else:
        return None  # Empate, no se genera señal
    
    # Crear y devolver la señal para la siguiente vela
    return Signal(
        pair=pair,
        direction=direction,
        strategy='mhi1_minoria'
    )