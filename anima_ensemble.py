#anima_ensemble.py
import numpy as np
from anima_logger import setup_logger

logger = setup_logger("anima_ensemble")
# Intentamos usar Numba; si no está disponible, caemos a versión Python pura
try:
    from numba import njit, prange
except ImportError:
    def _compute_net_gains(strategy_ids: np.ndarray, results: np.ndarray, payouts: np.ndarray, n_strategies: int) -> np.ndarray:
        gains = np.zeros(n_strategies, dtype=np.float64)
        for idx, r in zip(strategy_ids, results):
            gains[idx] += payouts[idx] if r == 1 else -payouts[idx]
        return gains
else:
    @njit(parallel=True)
    def _compute_net_gains(strategy_ids: np.ndarray, results: np.ndarray, payouts: np.ndarray, n_strategies: int) -> np.ndarray:
        gains = np.zeros(n_strategies, dtype=np.float64)
        for i in prange(results.shape[0]):
            idx = strategy_ids[i]
            if results[i] == 1:
                gains[idx] += payouts[idx]
            else:
                gains[idx] -= payouts[idx]
        return gains

def generate_ensemble_signal(
    signals,
    strategy_list: list,
    payout: float,
    weights=None
) -> dict:
    """
    Genera una señal agregada. Admite dict, list de dict o DataFrame como entrada.
    """
    # Normalize input to list of dicts
    if isinstance(signals, dict):
        records = [signals]
    elif isinstance(signals, list) and signals and isinstance(signals[0], dict):
        records = signals
    else:
        try:
            records = signals.to_dict(orient='records')
        except Exception:
            logger.error(f"Input no soportado para generate_ensemble_signal: {type(signals)}")
            records = []

    # Map strat names to indices
    strat_to_idx = {name: idx for idx, name in enumerate(strategy_list)}
    n = len(strategy_list)
    # Build arrays
    strategy_ids = []
    results = []
    directions = []
    for rec in records:
        s = rec.get('strategy')
        if s not in strat_to_idx:
            logger.warning(f"Estrategia desconocida descartada: {s}")
            continue
        strategy_ids.append(strat_to_idx[s])
        results.append(1 if rec.get('resultado')=='WIN' else 0)
        directions.append(1 if rec.get('direction')=='CALL' else -1)
    strategy_ids = np.array(strategy_ids, dtype=np.int64)
    results      = np.array(results,      dtype=np.int64)
    vote_vals    = np.array(directions,   dtype=np.float64)
    payouts      = np.full(n, payout,     dtype=np.float64)
    # Si no hay señales válidas, devolvemos ensemble neutro
    if strategy_ids.size == 0:
        default_w = np.full(n, 1.0/n, dtype=np.float64)
        logger.warning("No hay señales válidas; retornando ensemble neutro.")
        return {'direction': None, 'weights': default_w.tolist()}

    # Calcular o validar pesos
    if weights is None:
        net_gains = _compute_net_gains(strategy_ids, results, payouts, n)
        max_gain = np.max(net_gains)
        exp_vals = np.exp(net_gains - max_gain)
        weights = exp_vals / exp_vals.sum()
    else:
        w = np.array(weights, dtype=np.float64)
        if w.size != n:
            raise ValueError("Número de pesos distinto al de estrategias.")
        weights = w / w.sum()

    # Votación ponderada
    vote = float((vote_vals * weights[strategy_ids]).sum())

    direction = 'CALL' if vote >= 0 else 'PUT'
    return {'direction': direction, 'weights': weights.tolist()}
