# File: anima_core.py
import threading
import time
import os
import pandas as pd
import numpy as np
import logging
from anima_config import cargar_config
from anima_logger import setup_logger
from engine.signal_bus import SignalBus
from engine.worker_pool import StrategyWorker
from core.anima_broker import AnimaBroker, conectar_broker
from anima_db import DBHandler
from watchdog import BrokerWatchdog
from anima_autoconsciencia import AutoconscienciaFinanciera
from anima_ensemble import generate_ensemble_signal
from anima_rl_agent import AnimaTradingEnv, AnimaRLLightAgent
from anima_supervisor import SupervisorMetaCognitivo
from observability import signal_processing_time, error_counter, thread_heartbeat
import copy
import queue

logger = setup_logger("anima_core")

class AnimaCore:
    def __init__(self, stop_event: threading.Event):
        self.stop_event = stop_event
        self.config = cargar_config()
        self.pares = self.config.get("pairs", [])
        self.estrategias = self.config.get("estrategias", [])
        self.duracion = self.config.get("duracion", 1)

        self.supervisor = SupervisorMetaCognitivo(self.config)

        # Conexión al broker y keep-alive
        self.broker = conectar_broker(self.config["credenciales"], stop_event)

        # Bus de señales y workers
        self.bus = SignalBus()
        self.workers = []

        # Base de datos y autoconsciencia
        self.db = DBHandler()
        self.autoconsciencia = AutoconscienciaFinanciera(self.config)

        # Watchdog externo con reconexión que actualiza la instancia de broker
        def _reconnect_and_assign():
            new_sess = conectar_broker(self.config["credenciales"], self.stop_event)
            self.broker = new_sess
            return new_sess
        self.watchdog = BrokerWatchdog(
            session=self.broker,
            reconectar_funcion=_reconnect_and_assign,
            intervalo=self.config.get("watchdog_interval", 30)
        )
        # Arrancar watchdog y keep-alive threads
        self.watchdog_thread = threading.Thread(target=self.watchdog.iniciar, daemon=True)
        self.watchdog_thread.start()
        self.keep_thread     = threading.Thread(target=self._keepalive_loop, daemon=True)
        self.keep_thread.start()

        # Pesos optimizados
        path_pesos = "ga_results/best_weights.npy"
        if os.path.exists(path_pesos):
            try:
                self.best_weights = np.load(path_pesos)
                logger.info("Pesos óptimos cargados desde best_weights.npy")
            except Exception:
                self.best_weights = None
                logger.warning("Error cargando pesos óptimos; usando lógica estándar.")
        else:
            self.best_weights = None
            logger.warning("No se encontraron pesos optimizados; usando lógica estándar.")

        # RL Setup
        initial_balance = self.broker.get_balance()
        self.rl_env = AnimaTradingEnv(self.config, initial_balance=initial_balance)
        self.rl_agent = AnimaRLLightAgent(self.rl_env)
        self.rl_threshold = self.config.get("rl", {}).get("performance_threshold", -0.2)

        # Watchdog adicional eliminado: se usa solo la instancia con reassign callback

    def _keepalive_loop(self):
        interval = self.config.get("ping_interval", 10)
        while not self.stop_event.is_set():
            # Heartbeat para hilo keepalive
            thread_heartbeat.labels(thread='keepalive').set(time.time())
            try:
                self.broker.ping()
            except Exception as e:
                logger.warning(f"Ping fallido: {e}; reconectando broker...")
                try:
                    self.broker.conectar()
                    logger.info("Broker reconectado con éxito en keep-alive.")
                except Exception as ce:
                    logger.error(f"Fallo reconexión en keep-alive: {ce}")
            time.sleep(interval)

    def start_workers(self):
        for pair in self.pares:
            for estrategia in self.estrategias:
                cfg = copy.deepcopy(estrategia)
                # Protege la inyección de 'pair'
                params = cfg.get('params', {})
                params['pair'] = pair
                cfg['params'] = params
                worker = StrategyWorker(pair=pair, estrategia_cfg=cfg, bus=self.bus, stop_event=self.stop_event)
                worker.start()
                self.workers.append(worker)
                logger.info(f"Worker lanzado: {cfg['nombre']} sobre {pair}")

    def ejecutar_nucleo_tiempo_real(self):
        step = 0
        while not self.stop_event.is_set():
            try:
                senal = self.bus.get(timeout=1)
            except queue.Empty:
                continue

            try:
                # Medir tiempo de procesamiento de señal
                with signal_processing_time.time():
                    # — Normalizar señal a diccionario —
                    if isinstance(senal, dict):
                        sig = senal.copy()
                    elif hasattr(senal, "_asdict"):
                        sig = senal._asdict()
                    else:
                        sig = {k: getattr(senal, k) for k in ["timestamp","pair","strategy","direction","resultado"]
                               if hasattr(senal, k)}

                    # Renombra campos si vienen en otro idioma
                    if "nombre" in sig and "strategy" not in sig:
                        sig["strategy"] = sig.pop("nombre")
                    if "estrategia" in sig and "strategy" not in sig:
                        sig["strategy"] = sig.pop("estrategia")

                    # Asegurar columna ‘resultado’
                    sig.setdefault("resultado", "WIN")

                    # Crear DataFrame con campos estandarizados
                    df_s = pd.DataFrame([sig])
                    ensemble_out = generate_ensemble_signal(
                        df_s,
                        strategy_list=[e['nombre'] for e in self.estrategias],
                        payout=self.config.get('payout', 0.8),
                        weights=self.best_weights
                    )
                    # Inyectar señal de ensemble en el entorno RL
                    self.rl_env.set_ensemble(
                        ensemble_out['direction'],
                        ensemble_out['weights']
                    )
                    state = self.rl_env.get_observation()
                    action = self.rl_agent.select_action(state)
                    if self.rl_agent.recent_reward_avg < self.rl_threshold or action == 1:
                        decision = {'direction': ensemble_out['direction'], 'strategy': ensemble_out['weights']}
                    else:
                        decision = {'direction': None, 'strategy': None}
                    try:
                        self.db.registrar_rl_metric(
                            step=step,
                            action=action,
                            reward=0.0,
                            balance=self.broker.get_balance(),
                            ensemble_signal=ensemble_out['direction'],
                            weights=ensemble_out['weights'],
                            epsilon=self.rl_agent.epsilon
                        )
                    except Exception as e:
                        error_counter.labels(component='db').inc()
                        logger.error(f"Error registro RL métrica: {e}")
                    if decision['direction']:
                        datos = {
                            'timestamp': sig.get('timestamp'),
                            'pair':      sig.get('pair'),
                            'direction': decision['direction'],
                            'strategy':  sig.get('strategy')
                        }
                        self.ejecutar_operacion(datos)
            except Exception:
                # Contar cualquier error en procesamiento de señal
                error_counter.labels(component='core').inc()
                logger.exception("Error en ejecutar_nucleo_tiempo_real")
            finally:
                step += 1

    def ejecutar_operacion(self, datos: dict):
        """Ejecuta una operación usando el broker y obtiene el resultado."""
        par = datos.get('pair')
        direc = datos.get('direction')
        # Obtener monto de apuesta según nivel de martingala
        monto = datos.get('monto', self.supervisor.get_current_monto())
        tiempo = datos.get('duracion', self.config.get('duracion', self.duracion))
        ok, ticket = self.broker.comprar(par, direc, monto, tiempo)
        if not ok:
            logger.error(f"Fallo en broker.comprar para {par} {direc}")
            return None
        resultado = self.broker.check_win(ticket, timeout=self.config.get('timeout', None))
        logger.info(f"Resultado operación {par} {direc}: {resultado}")
        return resultado

    def run(self):
        """Inicia workers, hilo de señales y espera hasta shutdown."""
        # 1) Lanzar todos los workers
        self.start_workers()
        # 2) Crear y arrancar el hilo de procesamiento de señales
        self.signal_thread = threading.Thread(
            target=self.ejecutar_nucleo_tiempo_real,
            daemon=True
        )
        self.signal_thread.start()
        # 3) Esperar a que se marque el stop_event
        self.stop_event.wait()

    def shutdown(self):
        self.stop_event.set()
        try:
            self.broker.desconectar()
        except:
            pass
        logging.getLogger().info("AnimaCore detenido correctamente.")
