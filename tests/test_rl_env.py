import numpy as np
import pytest
from anima_rl_agent import AnimaTradingEnv


def test_reset_reproducibility():
    env1 = AnimaTradingEnv(config={}, seed=42)
    env2 = AnimaTradingEnv(config={}, seed=42)
    obs1, _ = env1.reset()
    obs2, _ = env2.reset()
    assert np.allclose(obs1, obs2), "Observations after reset with same seed should match"


def test_step_reproducibility():
    env1 = AnimaTradingEnv(config={}, seed=123)
    env2 = AnimaTradingEnv(config={}, seed=123)
    obs1, _ = env1.reset()
    obs2, _ = env2.reset()
    obs1_n, _, _, _, _ = env1.step(1)
    obs2_n, _, _, _, _ = env2.step(1)
    assert np.allclose(obs1_n, obs2_n), "Observations after step with same seed and action should match"