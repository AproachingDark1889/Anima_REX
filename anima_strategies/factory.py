# anima_strategies/factory.py
import importlib
from typing import Callable
import pandas as pd
from signal_model import Signal  # ← Importa directamente sin crear circularidad

def estrategia_factory(estrategia_cfg: dict) -> Callable[[pd.DataFrame], Signal | None]:
    """
    Devuelve una función que evalúa una estrategia específica.
    
    Esta función envuelve la función `generate_signal` del módulo correspondiente,
    inyectando los parámetros especificados.

    Args:
        estrategia_cfg: dict con 'nombre' y 'params'

    Returns:
        Callable que acepta un DataFrame y retorna una Signal o None.
    """
    nombre = estrategia_cfg['nombre']
    params = estrategia_cfg.get('params', {})
    modulo = importlib.import_module(f"anima_strategies.{nombre}")
    generate_signal_fn = modulo.generate_signal

    def wrapper(df: pd.DataFrame) -> Signal | None:
        return generate_signal_fn(df, params)

    return wrapper
