"""
Scheduler para ejecutar la optimización genética de forma programada.
Utiliza APScheduler para lanzar GAOptimizer.optimize() diariamente.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from core.anima_ga_optimizer import GAOptimizer
from anima_config import cargar_config

def schedule_daily_optimization(hour: int = 2, minute: int = 0) -> BackgroundScheduler:
    """
    Programa la optimización genética para que se ejecute cada día a la hora especificada.

    :param hour: hora local (0-23) para ejecutar el job
    :param minute: minuto (0-59) para ejecutar el job
    :return: instancia de BackgroundScheduler iniciada
    """
    # Cargar horario GA desde config.yml si existe
    cfg = cargar_config()
    sched = cfg.get('ga', {}).get('schedule', {})
    hour   = sched.get('hour',   hour)
    minute = sched.get('minute', minute)

    scheduler = BackgroundScheduler(timezone='America/Monterrey')
    scheduler.add_job(
        func=GAOptimizer().optimize,
        trigger='cron',
        hour=hour,
        minute=minute,
        id='ga_optimization_job',
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    print(f"[SCHEDULER] GA optimizer scheduled daily at {hour:02d}:{minute:02d}")
    return scheduler

if __name__ == '__main__':
    # Ejecución de prueba: programa el job y mantiene el proceso activo
    schedule_daily_optimization()
    print(f"[SCHEDULER] Iniciado a las {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    try:
        # Mantener vivo
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("[SCHEDULER] Detenido por señal de interrupción.")
