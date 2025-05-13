# evaluator.py
# Módulo para evaluar las señales históricas y determinar la mejor estrategia

from services.anima_signals_download import Signal
import pandas as pd

class Evaluator:
    """
    Evalúa los resultados de señales históricas para seleccionar la mejor estrategia.
    """

    def __init__(self, resultados: list[tuple[Signal, str]]):
        self.resultados = resultados  # Lista de tuplas (Signal, resultado)

    def contar_victorias_por_estrategia(self):
        conteo = {}
        for senal, resultado in self.resultados:
            nombre = senal.strategy
            if nombre not in conteo:
                conteo[nombre] = {'win': 0, 'loss': 0, 'empate': 0}
            if resultado == "WIN":
                conteo[nombre]['win'] += 1
            elif resultado == "LOSS":
                conteo[nombre]['loss'] += 1
            else:
                conteo[nombre]['empate'] += 1
        return conteo

    def mejor_estrategia(self):
        conteo = self.contar_victorias_por_estrategia()
        if not conteo:
            return None
        mejor = max(conteo.items(), key=lambda x: x[1]['win'])
        return mejor[0]  # Nombre de la estrategia
