# anima_signal_history.py
# Motor de análisis histórico de estrategias sobre múltiples pares

import pandas as pd
import logging
from anima_config import cargar_config
from anima_market import get_historical_ohlcv
from anima_strategies.factory import estrategia_factory
from signal_model import Signal

logger = logging.getLogger(__name__)

class SignalHistory:
    """
    Aplica todas las estrategias configuradas sobre todos los pares definidos,
    y genera un DataFrame de resultados para análisis o entrenamiento.
    """
    def __init__(self):
        self.config = cargar_config()
        self.pairs = self.config.get("pairs", [])
        self.estrategias = self.config.get("estrategias", [])
        self.timeframe = self.config.get("timeframe", "1m")
        self.start_date = self.config.get("start_date")
        self.end_date = self.config.get("end_date")
        self.signals = []

    def run(self) -> pd.DataFrame:
        """
        Ejecuta todas las estrategias sobre todos los pares en el rango definido.
        Retorna un DataFrame con las señales generadas.
        """
        for pair in self.pairs:
            logger.info(f"📊 Analizando histórico para {pair}")
            df = get_historical_ohlcv(pair, timeframe=self.timeframe, start_date=self.start_date, end_date=self.end_date)

            if df.empty or len(df) < 10:
                logger.warning(f"⚠️ Insuficientes datos para {pair}")
                continue

            for estrategia_cfg in self.estrategias:
                nombre = estrategia_cfg.get("nombre")
                params = estrategia_cfg.get("params", {})
                params["pair"] = pair  # Inyectamos el par en los parámetros
                logger.info(f"⚙️ Aplicando estrategia: {nombre} en {pair}")

                estrategia_fn = estrategia_factory(estrategia_cfg)

                for i in range(len(df)):
                    sub_df = df.iloc[:i+1].copy()
                    try:
                        signal = estrategia_fn(sub_df, params)
                        if signal:
                            self.signals.append({
                                "timestamp": sub_df.index[-1],
                                "pair": signal.pair,
                                "direction": signal.direction,
                                "strategy": signal.strategy
                            })
                    except Exception as e:
                        logger.error(f"❌ Error al aplicar {nombre} en {pair} (i={i}): {e}")

        return pd.DataFrame(self.signals)

