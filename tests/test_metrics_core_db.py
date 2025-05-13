import queue
import pytest
from prometheus_client import generate_latest
import core.anima_core as core_mod
from core.anima_core import AnimaCore, DBHandler

class DummyBroker:
    def get_balance(self): return 1000.0
    def comprar(self, *args, **kwargs): return True, 1
    def check_win(self, ticket, timeout=None): return 'WIN'
    def ping(self): pass
    def conectar(self): pass

class DummyBus:
    def __init__(self, stop_event):
        self.called = False
        self.stop_event = stop_event
    def get(self, timeout):
        if not self.called:
            self.called = True
            # Provide minimal fields for signal processing
            return {'timestamp': 0, 'pair': 'P1', 'strategy': 'S1', 'direction': 'CALL', 'resultado': 'WIN'}
        else:
            self.stop_event.set()
            raise queue.Empty()


def test_error_counter_db(monkeypatch):
    # Monkeypatch broker constructor
    monkeypatch.setattr(core_mod, 'conectar_broker', lambda creds, ev: DummyBroker())
    # Monkeypatch generate_ensemble_signal to return valid direction and weights
    monkeypatch.setattr(core_mod, 'generate_ensemble_signal', lambda df, strategy_list, payout, weights: {'direction': 'CALL', 'weights': [1.0]})
    # Monkeypatch DBHandler.registrar_rl_metric to throw
    monkeypatch.setattr(DBHandler, 'registrar_rl_metric', lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("db fail")))
    # Setup core with dummy bus and custom stop_event
    stop_event = core_mod.threading.Event()
    core = AnimaCore(stop_event)
    core.bus = DummyBus(stop_event)
    # Run signal processing (should catch DB error and increment counter)
    core.ejecutar_nucleo_tiempo_real()
    # Get metrics
    metrics = generate_latest()
    # Assert error_counter for component=db incremented
    assert b'error_count_total{component="db"} 1.0' in metrics
