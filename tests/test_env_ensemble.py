#test_env_ensemble.py
import numpy as np
import pytest
from anima_rl_agent import AnimaTradingEnv


def test_set_ensemble_and_observation():
    # Crear entorno con semilla fija
    env = AnimaTradingEnv(config={}, seed=123)

    # Inicialmente ens_dir y ga_wt deberían ser 0.0
    obs0, _ = env.reset()
    # obs0 tiene longitud 9; últimos índices -2 y -1 corresponden a ens_dir y ga_wt
    assert obs0[-2] == pytest.approx(0.0)
    assert obs0[-1] == pytest.approx(0.0)

    # Fijar señal de ensemble: CALL y pesos
    weights = [0.2, 0.8, 0.6]
    env.set_ensemble('CALL', weights)
    # La dirección CALL se mapea a 1.0 y peso medio a 0.533...
    assert env.ens_dir == pytest.approx(1.0)
    assert env.ga_wt == pytest.approx(np.mean(weights))

    # Verificar que reset() propaga esos valores en el vector
    obs1, _ = env.reset()
    assert obs1[-2] == pytest.approx(1.0)
    assert obs1[-1] == pytest.approx(np.mean(weights))

    # Cambiar a PUT con pesos vacíos
    env.set_ensemble('PUT', [])
    obs2, _ = env.reset()
    assert obs2[-2] == pytest.approx(-1.0)
    assert obs2[-1] == pytest.approx(0.0)

    # Valores intermedios en un paso
    weights2 = [0.4, 0.1]
    env.set_ensemble('PUT', weights2)
    obs3, _, _, _, _ = env.step(1)
    assert obs3[-2] == pytest.approx(-1.0)
    assert obs3[-1] == pytest.approx(np.mean(weights2))
