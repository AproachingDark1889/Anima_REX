#watchdog
import time
from anima_logger import setup_logger
import threading

logger = setup_logger("watchdog")

class BrokerWatchdog:
    def __init__(self, session, reconectar_funcion, intervalo=30):
        """
        :param session: Objeto de sesión IQ Option ya conectado
        :param reconectar_funcion: Función a llamar si la sesión está caída
        :param intervalo: Tiempo en segundos entre verificaciones
        """
        self.session = session
        self.reconectar_funcion = reconectar_funcion
        self.intervalo = intervalo
        # Flag para detener el loop
        self._stop_event = threading.Event()

    def verificar_conexion(self):
        try:
            self.session.get_balance()
            return True
        except Exception as e:
            logger.warning(f"Watchdog detectó desconexión: {e}")
            return False

    def iniciar(self):
        while not getattr(self, '_stop_event', threading.Event()).is_set():
            if not self.verificar_conexion():
                logger.warning("Intentando reconectar sesión...")
                self.session = self.reconectar_funcion()
                logger.info("Reconexión ejecutada.")
            time.sleep(self.intervalo)
        logger.info("BrokerWatchdog detenido.")

    def stop(self):
        """Marca el watchdog para que su loop de inicio termine."""
        self._stop_event.set()
