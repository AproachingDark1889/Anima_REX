import os
from datetime import datetime
import pandas as pd
import dask.dataframe as dd
from anima_config import cargar_config
from anima_db import DBHandler
from anima_ensemble import generate_ensemble_signal

def backtest_ensemble(start=None, end=None, output_dir="backtest_results"):
    """
    Ejecuta el backtest del ensemble dinámico usando señales y resultados reales.
    """
    os.makedirs(output_dir, exist_ok=True)
    cfg = cargar_config()
    payout = cfg.get('payout', 0.8)
    strategies = [e['nombre'] for e in cfg.get('estrategias', [])]

    # Cargar señales y operaciones
    db = DBHandler()
    df_signals = db.load_signals()
    df_ops     = db.load_operations()

    # Renombrar para unificar columna de resultado
    df_ops = df_ops.rename(columns={'result': 'resultado'})

    # Unir por timestamp, par y estrategia
    df = pd.merge(
        df_signals,
        df_ops[['timestamp', 'pair', 'strategy', 'resultado']],
        on=['timestamp', 'pair', 'strategy'],
        how='inner'
    )

    # Filtrar rango de fechas
    if start:
        df = df[df['timestamp'] >= pd.to_datetime(start)]
    if end:
        df = df[df['timestamp'] <= pd.to_datetime(end)]

    # Preparar Dask y esquema
    dd_df = dd.from_pandas(df, npartitions=os.cpu_count())
    meta  = df.head(0).copy()
    meta['ensemble_direction'] = pd.Series(dtype='object')

    # Procesar cada partición
    def process_partition(part: pd.DataFrame) -> pd.DataFrame:
        dfp = part.copy()
        ens = generate_ensemble_signal(dfp, strategies, payout)
        dfp['ensemble_direction'] = ens['direction']
        return dfp

    # Ejecutar paralelo con meta
    result = dd_df.map_partitions(process_partition, meta=meta).compute()

    # Guardar parquet de resultados
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"ensemble_backtest_{ts}.parquet")
    result.to_parquet(path, index=False)
    print(f"[BACKTEST] Resultados guardados en: {path}")

if __name__ == '__main__':
    print("[BACKTEST] Iniciando backtest paralelo del ensemble...")
    backtest_ensemble()
    print("[BACKTEST] Backtest completado.")
