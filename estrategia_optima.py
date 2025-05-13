from collections import defaultdict
from typing import List
from signal_model import Signal
from anima_db import DBHandler

def seleccionar_mejor_estrategia(historico: List[Signal], payout: float = 0.8, usar_db: bool = False) -> str | None:
    """
    Evalúa el histórico de señales y calcula cuál estrategia tuvo mejor ganancia neta.

    Args:
        historico: lista de señales ejecutadas con resultado y monto.
        payout: ganancia por operación ganada.
        usar_db: si True, también consulta datos desde la base de datos.

    Returns:
        Nombre de la estrategia más rentable.
    """
    ganancias_por_estrategia = defaultdict(float)

    for signal in historico:
        if not hasattr(signal, "resultado") or not hasattr(signal, "monto"):
            continue
        monto = signal.monto
        if signal.resultado == "WIN":
            ganancias_por_estrategia[signal.strategy] += monto * payout
        elif signal.resultado == "LOSS":
            ganancias_por_estrategia[signal.strategy] -= monto

    if usar_db:
        db = DBHandler()
        try:
            with db._conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT estrategia, resultado, monto FROM operaciones")
                for estrategia, resultado, monto in cursor.fetchall():
                    if resultado == "WIN":
                        ganancias_por_estrategia[estrategia] += monto * payout
                    elif resultado == "LOSS":
                        ganancias_por_estrategia[estrategia] -= monto
        except Exception as e:
            print(f"[Error DB] No se pudo acceder a operaciones históricas: {e}")

    if not ganancias_por_estrategia:
        return None

    estrategia_max = max(ganancias_por_estrategia.items(), key=lambda x: x[1])[0]
    return estrategia_max
