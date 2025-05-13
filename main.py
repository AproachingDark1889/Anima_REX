# File: main.py (versión restaurada sin basura)
from anima_logger import setup_logger
from observability import start_metrics_server  # Prometheus metrics
import signal, sys, threading, time
import logging

from anima_config import cargar_config
from setup_env import setup_environment
from anima_data import fetch_and_store_ohlcv
from services.anima_backtester import backtest_ensemble
from core.anima_scheduler import schedule_daily_optimization
from core.anima_core import AnimaCore

# Logging unificado
logger = setup_logger("main")
# Activar DEBUG logging global para capturar todos los detalles
logging.getLogger().setLevel(logging.DEBUG)
# Evento global para detener todos los loops
env_stop_event = threading.Event()

def main():
    # Init observability metrics server
    start_metrics_server(port=8000)
    # Load configuration with error handling
    try:
        cfg = cargar_config()
    except Exception as e:
        logger.error(f"Error cargando config.yml: {e}")
        sys.exit(1)

    # SIGINT handler
    def on_sigint(signum, frame):
        logger.info("SIGINT recibido: deteniendo scheduler y core...")
        env_stop_event.set()
    signal.signal(signal.SIGINT, on_sigint)

    scheduler = None
    # Fases de arranque con manejo de errores
    try:
        logger.info("Configurando entorno...")
        setup_environment()
    except Exception as e:
        logger.exception("Error en setup_environment: %s", e)
        sys.exit(1)
    try:
        logger.info("Ingesta OHLCV...")
        fetch_and_store_ohlcv(parquet=True, sqlite_store=True)
    except Exception as e:
        logger.exception("Error en fetch_and_store_ohlcv: %s", e)
    try:
        logger.info("Backtest ensemble...")
        backtest_ensemble()
    except Exception as e:
        logger.exception("Error en backtest_ensemble: %s", e)
    # Scheduler diario
    try:
        logger.info("Iniciando scheduler diario...")
        scheduler = schedule_daily_optimization()
        # Fallback si schedule_daily_optimization no devolvió scheduler
        if scheduler is None:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.start()
            logger.warning("schedule_daily_optimization no devolvió scheduler; arranqué uno por defecto.")
    except Exception as e:
        logger.exception("Error en schedule_daily_optimization: %s", e)

    # Bucle de resiliencia para core
    while not env_stop_event.is_set():
        core = AnimaCore(env_stop_event)
        try:
            core.run()
        except Exception as e:
            logger.exception("Crash en AnimaCore: %s. Reinciando en 30s", e)
            core.shutdown()
            time.sleep(30)
        else:
            break

    # Shutdown ordenado: primero scheduler, luego core
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler detenido.")
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {e}")
    core.shutdown()
    logger.info("Core detenido.")
    logger.info("Shutdown completo.")
    # Exit code 0 if stopped by SIGINT, else 1
    sys.exit(0 if env_stop_event.is_set() else 1)

if __name__ == '__main__':
    main()
