#anima_broker.py
import time
import logging
import threading
from typing import List, Optional
from libs.iqoptionapi_stable import IQ_Option

from anima_utils import parse_timeframe

logger = logging.getLogger(__name__)

# Decorador para asegurar conexión antes de ejecutar métodos sensibles
def ensure_connection(method):
    def wrapper(self, *args, **kwargs):
        # Protege reconexión con lock de instancia
        with self._lock:
            if not self.Iq.check_connect():
                status, reason = self.Iq.connect()
                if not status:
                    raise ConnectionError(f"Conexión fallida: {reason}")
                self._wait_ready(timeout=5)
        return method(self, *args, **kwargs)
    return wrapper


class AnimaBroker:
    """Controlador principal de conexión, órdenes y consulta de IQ Option para Anima REX."""

    def _wait_ready(self, timeout: float = 5.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                _ = self.Iq.get_balance()
                return
            except Exception:
                time.sleep(0.2)
        raise ConnectionError("IQ Option no respondió dentro del tiempo límite.")

    def __init__(self, iq: IQ_Option, demo: bool = True, stop_event: Optional[threading.Event] = None):
        """
        Args:
            iq: Instancia autenticada de IQ_Option.
            demo: `True` para cuenta práctica, `False` para real.
            stop_event: Evento para detener operaciones largas (opcional).
        """
        self.Iq = iq
        self.demo = demo
        self.stop_event = stop_event or threading.Event()
        # Lock para proteger reconexiones y evitar serializar todas las llamadas
        self._lock = threading.Lock()

        status, reason = self.Iq.connect()
        if not status:
            raise ConnectionError(f"Conexión fallida: {reason}")

        self._wait_ready(timeout=5)
        # Establecer tipo de cuenta correctamente (IQ Option espera mayúsculas)
        self.Iq.change_balance("PRACTICE" if demo else "REAL")
        logger.info(f"Broker conectado en modo {'DEMO' if demo else 'REAL'}")
        # Log de diagnóstico de cuenta
        logger.info(f"[DEBUG] Tipo de cuenta: {self.Iq.get_balance_mode()} | Balance actual: {self.Iq.get_balance()}")

    # ---------- Datos de mercado -------------------------------------------------

    @ensure_connection
    def fetch_ohlcv(self, symbol: str, timeframe: str, since: int, until: Optional[int] = None) -> List[list]:
        """Obtiene datos OHLCV para un `symbol` y `timeframe` dentro del rango [`since`, `until`].

        Args:
            symbol: Par de divisas, p. ej. "EURUSD".
            timeframe: Timeframe textual ("1m", "5m", etc.).
            since: Timestamp Unix (segundos) de inicio.
            until: Timestamp Unix (segundos) final. Si es None se usa `time.time()`.

        Returns:
            Lista de velas en formato `[timestamp, open, high, low, close, volume]`.
            Devuelve lista vacía si no se reciben datos.
        """
        try:
            tf_seconds = parse_timeframe(timeframe)
        except Exception as e:
            logger.error(f"Timeframe inválido: {timeframe} ({e})")
            raise

        end_ts = until or int(time.time())
        if end_ts <= since:
            raise ValueError(f"'until' ({end_ts}) debe ser mayor que 'since' ({since})")

        count = (end_ts - since) // tf_seconds + 1
        if count <= 0:
            raise ValueError(
                f"El rango de tiempo es demasiado corto para el timeframe '{timeframe}'")

        try:
            start_time = time.time()
            candles = self.Iq.get_candles(symbol, tf_seconds, count, end_ts)
            latency = time.time() - start_time
            logger.info(f"Latencia de get_candles: {latency:.2f} segundos")
        except Exception as e:
            if isinstance(e, dict) and e.get("code") == "TooManyRequests":
                logger.warning("Demasiadas solicitudes. Aplicando back-off de 2 minutos.")
                time.sleep(120)
                return self.fetch_ohlcv(symbol, timeframe, since, until)
            logger.error(f"Error al obtener velas: {e}")
            raise

        if not candles:
            logger.warning("Sin datos OHLCV para %s", symbol)
            return []

        return [[c['from'], c['open'], c['max'], c['min'], c['close'], c['volume']] for c in candles]

    @ensure_connection
    def comprar(self, par: str, direccion: str, monto: float, tiempo: int) -> tuple[bool, Optional[int]]:
        """Realiza una operación de compra en IQ Option.

        Args:
            par: Par de divisas, p. ej. "EURUSD".
            direccion: "call" para compra, "put" para venta.
            monto: Monto de la operación.
            tiempo: Duración de la operación en minutos.

        Returns:
            Tuple con estado de la operación y ID de la orden.
        """
        direccion = direccion.strip().lower()
        if direccion not in ("call", "put"):
            raise ValueError("direccion debe ser 'call' o 'put'")

        if self.get_balance() < monto:
            raise ValueError("Saldo insuficiente para realizar la operación.")

        # Reforzar logs y manejo de errores en buy_digital_spot
        # Debug de parámetros para buy_digital_spot
        logger.debug(f"[DEBUG] Enviando a buy_digital_spot => par={par}, monto={monto}, direccion={direccion}, tiempo={tiempo}")
        logger.info(f"Enviando operación: {direccion.upper()} {par} | ${monto} | {tiempo}m")
        try:
            result = self.Iq.buy_digital_spot(par, monto, direccion, tiempo)

            if not isinstance(result, tuple):
                last_error = getattr(self.Iq, 'get_digital_spot_error', lambda: 'Desconocido')()
                logger.error(f"Error al realizar la operación (tipo inválido): {last_error}")
                return False, None

            status, id_op = result
            if not status:
                last_error = getattr(self.Iq, 'get_digital_spot_error', lambda: 'Desconocido')()
                logger.error(f"Error al realizar la operación (rechazada): {last_error}")
                return False, None

            logger.info(f"ORDEN EJECUTADA  → {par} | {direccion.upper()} | ${monto} | {tiempo}m")
            return True, id_op

        except Exception as e:
            logger.exception(f"Excepción crítica en broker.comprar para {par} {direccion}: {e}")
            return False, None

    def check_win(self, ticket_id: int, timeout: Optional[int] = None):
        """Verifica el resultado de una operación y devuelve la ganancia/pérdida."""
        logger.info("Esperando resultado para ID: %s", ticket_id)
        start = time.time()
        while not self.stop_event.is_set():
            res = self.Iq.check_win_digital_v2(ticket_id)

            # 1️⃣  Aún sin respuesta
            if res is None:
                if timeout and time.time() - start > timeout:
                    logger.warning("Timeout esperando resultado.")
                    return None
                time.sleep(1)
                continue

            check, win = res

            # 2️⃣  Operación cerrada
            if check:
                logger.info("Resultado: %s  $%.2f",
                            "GANANCIA" if win > 0 else "PÉRDIDA", win)
                return win

            # 3️⃣  Vela todavía abierta
            if win is None:
                if timeout and time.time() - start > timeout:
                    logger.warning("Timeout esperando resultado.")
                    return None
                time.sleep(1)
                continue

            # 4️⃣  Estado intermedio desconocido (ej. win negativo)
            logger.debug("Intermedio win=%s", win)
            time.sleep(1)

        logger.warning("check_win detenido por evento de parada.")
        return None

    # ---------- Gestión de conexión ---------------------------------------------
    def desconectar(self):
        try:
            if self.Iq and self.Iq.check_connect():
                self.Iq.close()
        finally:
            logger.info("Conexión cerrada con IQ Option.")

    def get_balance(self) -> float:
        return self.Iq.get_balance()

    def ping(self):
        _ = self.get_balance(); return True

    def conectar(self):
        status, reason = self.Iq.connect()
        if not status:
            raise ConnectionError(f"Fallo al reconectar: {reason}")


def conectar_broker(cred: dict, stop_event: Optional[threading.Event] = None) -> "AnimaBroker":
    """
    Helper para crear un `AnimaBroker` autenticado.

    Args:
        cred: Diccionario con claves `email`, `password` y opcional `demo` (bool).
        stop_event: Evento opcional para detener operaciones largas.

    Returns:
        Instancia lista para usar de `AnimaBroker`.
    """
    if not {"email", "password"} <= cred.keys():
        raise ValueError("Faltan credenciales: email y/o password")
    iq = IQ_Option(cred["email"], cred["password"])
    demo = cred.get("demo", True)
    return AnimaBroker(iq, demo, stop_event)
