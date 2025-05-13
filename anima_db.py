# anima_db.py
"""
Módulo de gestión de base de datos para Anima Rex.
Proporciona interfaces para:
  - Registrar señales generadas por las estrategias
  - Registrar operaciones ejecutadas
  - Registrar errores en la ejecución
  - Cargar señales y operaciones para análisis y backtesting
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime
from anima_config import cargar_config


class DBHandler:
    def __init__(self, db_path: str = None):
        cfg = cargar_config()
        base_dir = cfg.get('db_dir', 'data/sqlite')
        os.makedirs(base_dir, exist_ok=True)
        self.db_path = db_path or os.path.join(base_dir, 'operations.db')
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Tabla de señales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    pair TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    nivel INTEGER,
                    monto REAL,
                    metadata TEXT
                );
            ''')
            # Tabla de operaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    pair TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    result TEXT NOT NULL,
                    monto REAL NOT NULL,
                    nivel INTEGER,
                    balance_before REAL,
                    balance_after REAL
                );
            ''')
            # Tabla de métricas RL
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rl_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    step INTEGER,
                    action INTEGER,
                    reward REAL,
                    balance REAL,
                    ensemble_signal TEXT,
                    weights_mean REAL,
                    epsilon REAL
                );
            ''')
            # Tabla de errores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL
                );
            ''')

    def registrar_signal(self, pair: str, strategy: str, direction: str,
                          nivel: int = None, monto: float = None, metadata: str = None):
        """
        Inserta una señal en la tabla signals.
        """
        ts = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO signals (timestamp, pair, strategy, direction, nivel, monto, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (ts, pair, strategy, direction, nivel, monto, metadata)
            )

    def registrar_operacion(self, pair: str, strategy: str, result: str,
                             monto: float, nivel: int = None,
                             balance_before: float = None, balance_after: float = None):
        """
        Inserta una operación en la tabla operations.
        """
        ts = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO operations (timestamp, pair, strategy, result, monto, nivel, balance_before, balance_after) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (ts, pair, strategy, result, monto, nivel, balance_before, balance_after)
            )

    def registrar_error(self, module: str, message: str):
        """
        Inserta un error en la tabla errors.
        """
        ts = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO errors (timestamp, module, message) VALUES (?, ?, ?)',
                (ts, module, message)
            )

    def registrar_rl_metric(self, step: int, action: int, reward: float, balance: float,
                             ensemble_signal: str, weights: list, epsilon: float):
        """
        Inserta una métrica de RL en la tabla rl_metrics.
        """
        ts = datetime.utcnow().isoformat()
        weights_mean = float(sum(weights) / len(weights)) if weights else 0.0
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    '''INSERT INTO rl_metrics (timestamp, step, action, reward, balance, ensemble_signal, weights_mean, epsilon)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?);''',
                    (ts, step, action, reward, balance, ensemble_signal, weights_mean, epsilon)
                )
        except Exception as e:
            # Registrar error de base de datos
            print(f"[Error DB rl_metrics] {e}")

    def load_signals(self, since: str = None) -> pd.DataFrame:
        """
        Carga señales de la tabla signals.
        :param since: ISO timestamp para filtrar (opcional)
        :return: DataFrame con columnas [timestamp, pair, strategy, direction, nivel, monto, metadata]
        """
        query = 'SELECT timestamp, pair, strategy, direction, nivel, monto, metadata FROM signals'
        if since:
            query += f" WHERE timestamp >= '{since}'"
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn, parse_dates=['timestamp'])
        return df

    def load_operations(self, since: str = None) -> pd.DataFrame:
        """
        Carga operaciones de la tabla operations.
        :param since: ISO timestamp para filtrar (opcional)
        :return: DataFrame con columnas [timestamp, pair, strategy, result, monto, nivel, balance_before, balance_after]
        """
        query = 'SELECT timestamp, pair, strategy, result, monto, nivel, balance_before, balance_after FROM operations'
        if since:
            query += f" WHERE timestamp >= '{since}'"
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql(query, conn, parse_dates=['timestamp'])
        return df

    def load_ohlcv(self, symbol: str, timeframe: str = None) -> pd.DataFrame:
        """
        Carga datos OHLCV desde la base de datos ohlcv.sqlite para un símbolo.
        """
        import sqlite3
        import pandas as pd
        db_path = 'ohlcv.sqlite'
        query = 'SELECT timestamp, open, high, low, close, volume, timeframe FROM ohlcv WHERE symbol = ?'
        params = [symbol]
        if timeframe:
            query += ' AND timeframe = ?'
            params.append(timeframe)
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn, params=params, parse_dates=['timestamp'])
        conn.close()
        return df


if __name__ == '__main__':
    # Prueba rápida de DBHandler
    print('[DB] Prueba de DBHandler iniciada')
    db = DBHandler()
    db.registrar_signal('EURUSD', 'test_strategy', 'CALL', nivel=0, monto=1.0)
    db.registrar_operacion('EURUSD', 'test_strategy', 'WIN', monto=1.0, nivel=0, balance_before=100, balance_after=101)
    df_signals = db.load_signals()
    df_ops = db.load_operations()
    print(df_signals.head())
    print(df_ops.head())
    print('[DB] Prueba de DBHandler completada')
