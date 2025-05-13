import os
import pickle
import numpy as np
import pytest
from anima_rl_agent import AnimaTradingEnv, AnimaRLLightAgent

def test_migration_from_v1(tmp_path, monkeypatch):
    # Trabajar en directorio temporal
    monkeypatch.chdir(tmp_path)

    # Crear archivos v1: q_table.pkl y epsilon.npy
    old_q = {'a': np.array([1, 2, 3])}
    with open(tmp_path / 'q_table.pkl', 'wb') as f:
        pickle.dump(old_q, f)
    np.save(tmp_path / 'epsilon.npy', np.array(0.42))

    # Instanciar agente (debería migrar automáticamente a v2)
    env = AnimaTradingEnv(config={}, seed=0)
    agent = AnimaRLLightAgent(env, seed=0)

    # Debe existir rl_state.pkl v2
    state_path = tmp_path / 'rl_state.pkl'
    assert state_path.exists(), "No se creó rl_state.pkl"

    # Cargar contenido
    with open(state_path, 'rb') as f:
        data = pickle.load(f)
    assert data['version'] == 2
    # Q-table debe coincidir
    assert 'a' in data['q_table']
    assert np.array_equal(data['q_table']['a'], old_q['a'])
    # Epsilon debe coincidir
    assert data['epsilon'] == pytest.approx(0.42)

    # Los archivos v1 originales deben haber sido borrados
    assert not (tmp_path / 'q_table.pkl').exists()
    assert not (tmp_path / 'epsilon.npy').exists()


def test_load_v2_direct(tmp_path, monkeypatch):
    # Trabajar en directorio temporal
    monkeypatch.chdir(tmp_path)

    # Crear rl_state.pkl v2 manualmente
    original = {'x': np.array([9, 8, 7])}
    versioned = {'version': 2, 'q_table': original, 'epsilon': 0.77}
    with open(tmp_path / 'rl_state.pkl', 'wb') as f:
        pickle.dump(versioned, f)

    # Instanciar agente (debe cargar directamente v2)
    env = AnimaTradingEnv(config={}, seed=1)
    agent = AnimaRLLightAgent(env, seed=1)

    # Los valores del agente deben coincidir con los del archivo
    assert 'x' in agent.q_table
    assert np.array_equal(agent.q_table['x'], original['x'])
    assert agent.epsilon == pytest.approx(0.77)


def test_save_on_learn(tmp_path, monkeypatch):
    # Trabajar en directorio temporal
    monkeypatch.chdir(tmp_path)

    env = AnimaTradingEnv(config={}, seed=2)
    agent = AnimaRLLightAgent(env, seed=2)

    # Configurar estado inicial
    state_key = tuple((np.zeros(7) * 10).astype(int))
    agent.q_table = {state_key: np.array([5, 6, 7])}
    agent.epsilon = 0.55

    # Llamar learn() con done=True para forzar persistencia
    agent.learn(
        state=np.zeros(7),
        action=0,
        reward=0.0,
        next_state=np.zeros(7),
        done=True
    )

    # Debe existir rl_state.pkl actualizado
    state_path = tmp_path / 'rl_state.pkl'
    assert state_path.exists(), "No se guardó rl_state.pkl tras learn()"

    with open(state_path, 'rb') as f:
        data = pickle.load(f)
    assert data['version'] == 2
    # Q-table debería contener la clave configurada y coincidir con el estado del agente
    assert state_key in data['q_table']
    assert np.array_equal(data['q_table'][state_key], agent.q_table[state_key])
    # Epsilon debería coincidir
    assert data['epsilon'] == pytest.approx(agent.epsilon)
