#anima_rl_agent.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from collections import deque
from anima_logger import setup_logger
logger = setup_logger("anima_rl_agent")
from anima_config import cargar_config
import time
import traceback
from typing import Optional, Tuple, Dict, Any
import pickle
import os
from typing import List

class AnimaTradingEnv(gym.Env):
    """
    Entorno de trading RL ligero.
    Observaciones: últimos 3 resultados (0/1), hora normalizada, saldo relativo, señal ensemble, media de pesos GA.
    Acciones: 0=rechazar, 1=aceptar, 2=cambiar estrategia, 3=ajustar martingala, 4=suspender.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, config, initial_balance=1000.0, seed=None):
        super(AnimaTradingEnv, self).__init__()
        self.config = config
        # Observations now incluyen dos placeholders y atributos de ensemble: [3 resultados, hora, saldo_rel, placeholder1, placeholder2, ens_dir, ga_wt]
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(9,), dtype=np.float32)
        self.action_space = spaces.Discrete(5)
        self.result_history = deque(maxlen=3)
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.current_step = 0
        self.done = False
        # RNG para reproducibilidad
        self.rng = np.random.default_rng(seed)
        # Estado del ensemble (dirección y peso medio)
        self.ens_dir: float = 0.0
        self.ga_wt: float = 0.0
        self.reset()

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.result_history.clear()
        for _ in range(3):
            self.result_history.append(0)
        self.balance = self.initial_balance
        self.current_step = 0
        self.done = False
        obs = self._get_observation()
        return obs, {}

    def _get_observation(self):
        r = list(self.result_history)
        hour = float(self.current_step % 24) / 23.0
        saldo_rel = (self.balance - self.initial_balance) / self.initial_balance
        # Placeholder dims para futuras características
        placeholder1 = 0.0
        placeholder2 = 0.0
        # Observación extendida con ensemble dinámico
        return np.array(r + [hour, saldo_rel, placeholder1, placeholder2, self.ens_dir, self.ga_wt], dtype=np.float32)

    def get_observation(self):
        """Public wrapper for the internal observation method."""
        return self._get_observation()

    def step(self, action) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        # Ejecuta acción y devuelve (obs, reward, terminated, truncated, info)
        reward = 0.0
        result = self.rng.choice([1, -1])
        if action == 0:
            reward = -0.1 if result == 1 else 0.1
        elif action == 1:
            reward = 1.0 if result == 1 else -1.0
            self.balance += reward * self.initial_balance * 0.01
        else:
            reward = -0.05
        self.result_history.append(1 if result == 1 else 0)
        self.current_step += 1
        if self.current_step >= 100:
            self.done = True
        obs = self._get_observation()
        info: Dict[str, Any] = {'balance': self.balance}
        terminated = self.done
        truncated = False
        return obs, reward, terminated, truncated, info

    def render(self, mode='human'):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}")
    def set_ensemble(self, direction: str, weights: List[float]) -> None:
        """
        Actualiza la señal de ensemble y el peso medio.
        direction: 'CALL' o 'PUT'
        weights: lista de floats
        """
        dir_up = direction.upper() == 'CALL'
        dir_down = direction.upper() == 'PUT'
        self.ens_dir = 1.0 if dir_up else -1.0 if dir_down else 0.0
        self.ga_wt = float(np.mean(weights)) if weights else 0.0

class AnimaRLLightAgent:
    """
    Agente RL ligero (Q-learning) con epsilon-greedy.
    epsilon: probabilidad de exploración inicial.
    """
    def __init__(self, env: AnimaTradingEnv, lr=0.1, gamma=0.99,
                 epsilon=1.0, eps_decay=0.995, eps_min=0.1, seed: Optional[int] = None):
        self.env = env
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.eps_decay = eps_decay
        self.eps_min = eps_min
        # Cargar estado RL versionado (v2) o migrar desde v1 si existen archivos antiguos
        state_file = 'rl_state.pkl'
        if os.path.exists(state_file):
            try:
                with open(state_file, 'rb') as f:
                    data = pickle.load(f)
                if data.get('version') == 2:
                    self.q_table = data.get('q_table', {})
                    self.epsilon = data.get('epsilon', self.epsilon)
                    logger.info(f"Estado RL cargado de {state_file}")
                else:
                    raise ValueError("Versión RL no soportada")
            except Exception:
                logger.exception(f"Error cargando estado RL desde {state_file}, reiniciando nuevo estado")
                self.q_table = {}
        else:
            # migrar archivos v1: q_table.pkl y epsilon.npy
            old_q_file = 'q_table.pkl'
            old_eps_file = 'epsilon.npy'
            if os.path.exists(old_q_file) or os.path.exists(old_eps_file):
                # cargar viejo formato
                try:
                    q_old = {}
                    if os.path.exists(old_q_file):
                        with open(old_q_file, 'rb') as f:
                            q_old = pickle.load(f)
                    eps_old = self.epsilon
                    if os.path.exists(old_eps_file):
                        eps_old = float(np.load(old_eps_file))
                    # escribir nuevo rl_state.pkl
                    data = {'version': 2, 'q_table': q_old, 'epsilon': eps_old}
                    with open(state_file, 'wb') as f:
                        pickle.dump(data, f)
                    # eliminar antiguos
                    for p in (old_q_file, old_eps_file):
                        if os.path.exists(p): os.remove(p)
                    self.q_table = q_old
                    self.epsilon = eps_old
                    logger.info(f"Migración RL v1->v2 completada, estado en {state_file}")
                except Exception:
                    logger.exception("Error migrando estado RL de v1 a v2")
                    self.q_table = {}
            else:
                self.q_table = {}
        # RNG para reproducibilidad en exploración
        self.rng = np.random.default_rng(seed)
        self.rewards_window = deque(maxlen=10)

    def _state_to_key(self, state: np.ndarray) -> Tuple[int, ...]:
        # Discretizar cada dimensión del estado en bins configurables para reducir colisiones
        # Leer número de bins desde config o usar 10 por dimensión
        default_bins = [10] * len(state)
        bins = np.array(self.env.config.get('rl', {}).get('state_bins', default_bins))
        # Clip al rango [-1,1] para evitar outliers
        clipped = np.clip(state, -1.0, 1.0)
        # Transformar a [0, bins] índice entero
        discretized = np.floor((clipped + 1.0) * bins / 2.0).astype(int)
        # Asegurar rango válido [0, bins]
        discretized = np.minimum(discretized, bins)
        discretized = np.maximum(discretized, 0)
        return tuple(discretized.tolist())

    def select_action(self, state):
        key = self._state_to_key(state)
        if self.rng.random() < self.epsilon or key not in self.q_table:
            # exploración aleatoria reproducible
            return self.env.action_space.sample()  # type: ignore[attr-defined]
        return int(np.argmax(self.q_table[key]))

    def learn(self, state, action, reward, next_state, done):
        key = self._state_to_key(state)
        next_key = self._state_to_key(next_state)
        self.q_table.setdefault(key, np.zeros(self.env.action_space.n))
        self.q_table.setdefault(next_key, np.zeros(self.env.action_space.n))
        q_current = self.q_table[key][action]
        q_next = 0 if done else np.max(self.q_table[next_key])
        target = reward + self.gamma * q_next
        self.q_table[key][action] += self.lr * (target - q_current)
        self.rewards_window.append(reward)
        if done:
            # actualizar epsilon
            self.epsilon = max(self.eps_min, self.epsilon * self.eps_decay)
            # persistir estado RL v2
            try:
                state_file = 'rl_state.pkl'
                data = {'version': 2, 'q_table': self.q_table, 'epsilon': self.epsilon}
                with open(state_file, 'wb') as f:
                    pickle.dump(data, f)
                logger.info(f"Estado RL guardado en {state_file}")
            except Exception:
                logger.exception("Error guardando estado RL v2")

    @property
    def recent_reward_avg(self):
        if not self.rewards_window:
            return 0.0
        return sum(self.rewards_window) / len(self.rewards_window)

