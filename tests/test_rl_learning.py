import numpy as np
import pytest
from anima_rl_agent import AnimaTradingEnv, AnimaRLLightAgent


def test_learn_q_update():
    # Crear entorno y agente con semilla fija
    env = AnimaTradingEnv(config={}, seed=0)
    agent = AnimaRLLightAgent(env, lr=0.1, gamma=0.99, epsilon=0.0, eps_decay=1.0, eps_min=0.0, seed=0)

    # Estado dummy uniforme
    state = np.zeros(env.observation_space.shape, dtype=np.float32)
    next_state = np.zeros(env.observation_space.shape, dtype=np.float32)
    action = 0
    reward = 1.0

    # Antes de learn, q_table no tiene la key
    state_key = agent._state_to_key(state)
    assert state_key not in agent.q_table

    # Ejecutar learn() sin terminar episodio
    agent.learn(state, action, reward, next_state, done=False)

    # Tras learn, debe existir la key en q_table
    assert state_key in agent.q_table
    # Calcular Q esperado: lr * (reward + gamma*0 - current)
    expected_q = 0.1 * (reward + 0.99 * 0 - 0)
    np.testing.assert_allclose(agent.q_table[state_key][action], expected_q, rtol=1e-6)


def test_exploitation_after_learning():
    env = AnimaTradingEnv(config={}, seed=0)
    agent = AnimaRLLightAgent(env, lr=0.1, gamma=0.99, epsilon=1.0, eps_decay=1.0, eps_min=0.0, seed=0)

    state = np.zeros(env.observation_space.shape, dtype=np.float32)
    next_state = np.zeros(env.observation_space.shape, dtype=np.float32)

    # Aprender: acción 1 recibe mejor recompensa
    agent.learn(state, 0, reward=0.0, next_state=next_state, done=False)
    agent.learn(state, 1, reward=1.0, next_state=next_state, done=False)

    # Forzar explotación
    agent.epsilon = 0.0
    chosen = agent.select_action(state)
    assert chosen == 1, "El agente debe elegir la acción con mayor Q-value"