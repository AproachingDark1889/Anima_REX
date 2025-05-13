import pytest
from prometheus_client import generate_latest, CollectorRegistry, core
import data_utils
from anima_data import AnimaData
from threading import Event


def test_error_counter_increment(monkeypatch):
    """
    Simula una excepción en AnimaData.fetch_and_store y verifica que
    error_counter{component="ohlcv_ingestion"} incremente.
    """
    # Resetear métricas en un registry limpio
    registry = CollectorRegistry()
    # Recrar métrica en data_utils con registry global, así generate_latest leerá del default
    # Forzamos fetch_and_store lance
    class BrokenDM(AnimaData):
        def __init__(self, broker):
            super().__init__(broker)
        def fetch_and_store(self, *args, **kwargs):
            raise RuntimeError("simulated failure")

    # Parchar AnimaData para devolver BrokenDM
    monkeypatch.setattr(data_utils, 'AnimaData', lambda broker: BrokenDM(broker))
    # Ejecutar la función; debería capturar la excepción y no propagarse
    data_utils.fetch_and_persist_ohlcv()
    # Extraer métricas actuales
    metrics_output = generate_latest()
    # Verificar contador de errores para ohlcv_ingestion es 1
    assert b'error_count_total{component="ohlcv_ingestion"} 1.0' in metrics_output
