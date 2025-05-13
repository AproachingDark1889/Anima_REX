import time
import pytest
import data_utils
from threading import Event


class DummyDataManager:
    def __init__(self):
        self.called = False
        self.call_args = None

    def fetch_and_store(self, symbol, timeframe, since, until, parquet, sqlite_store):
        self.called = True
        self.call_args = {
            'symbol': symbol,
            'timeframe': timeframe,
            'since': since,
            'until': until,
            'parquet': parquet,
            'sqlite_store': sqlite_store
        }


class DummyBroker:
    pass


def test_fetch_and_persist_default(monkeypatch):
    # Simular tiempo fijo
    monkeypatch.setattr(time, 'time', lambda: 1000)
    # Configuración por defecto
    config = {'mercado': {'par': 'AAA', 'timeframe': '5m', 'minutos': 10}, 'credenciales': {'key': 'val'}}
    monkeypatch.setattr(data_utils, 'cargar_config', lambda: config)
    # Parchar broker
    def fake_conectar_broker(creds, stop_event):
        assert creds == config['credenciales']
        assert isinstance(stop_event, Event)
        return DummyBroker()
    monkeypatch.setattr(data_utils, 'conectar_broker', fake_conectar_broker)
    # Parchar DataManager
    dummy_dm = DummyDataManager()
    monkeypatch.setattr(data_utils, 'AnimaData', lambda broker: dummy_dm)

    # Ejecutar función
    data_utils.fetch_and_persist_ohlcv()

    # Validar llamadas
    assert dummy_dm.called is True
    args = dummy_dm.call_args
    assert args['symbol'] == 'AAA'
    assert args['timeframe'] == '5m'
    assert args['since'] == 1000 - 10 * 60
    assert args['until'] == 1000
    assert args['parquet'] is True
    assert args['sqlite_store'] is True


def test_fetch_and_persist_explicit(monkeypatch):
    # Simular tiempo fijo
    monkeypatch.setattr(time, 'time', lambda: 2000)
    # Configuración inicial (no se usa par de mercado)
    config = {'mercado': {'par': 'BBB', 'timeframe': '1h', 'minutos': 5}, 'credenciales': {}}
    monkeypatch.setattr(data_utils, 'cargar_config', lambda: config)
    monkeypatch.setattr(data_utils, 'conectar_broker', lambda c, e: DummyBroker())
    dummy_dm = DummyDataManager()
    monkeypatch.setattr(data_utils, 'AnimaData', lambda broker: dummy_dm)

    # Llamar con parámetros explícitos
    data_utils.fetch_and_persist_ohlcv(
        symbol='CCC', timeframe='15m', minutos=2,
        parquet=False, sqlite_store=False
    )

    assert dummy_dm.called is True
    args = dummy_dm.call_args
    assert args['symbol'] == 'CCC'
    assert args['timeframe'] == '15m'
    assert args['since'] == 2000 - 2 * 60
    assert args['until'] == 2000
    assert args['parquet'] is False
    assert args['sqlite_store'] is False
