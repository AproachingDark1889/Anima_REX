# anima_ga_optimizer.py
"""
Optimización de pesos de ensemble mediante Algoritmo Genético.
"""
import os
import random
import numpy as np
from datetime import datetime
from anima_config import cargar_config
from anima_db import DBHandler
from anima_ensemble import _compute_net_gains

class GAOptimizer:
    def __init__(self, population_size=20, generations=10, mutation_rate=0.1):
        self.config = cargar_config()
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
    def __init__(self):
        self.config = cargar_config()
        ga_cfg = self.config.get('ga', {})
        # Leer parámetros GA desde config.yml (o usar valores por defecto)
        self.population_size = ga_cfg.get('population_size', 20)
        self.generations     = ga_cfg.get('generations', 10)
        self.mutation_rate   = ga_cfg.get('mutation_rate', 0.1)
        self.strategies = [e['nombre'] for e in self.config.get('estrategias', [])]
        self.payout = self.config.get('payout', 0.8)
        self.db = DBHandler()

    def _generate_individual(self):
        """Genera un vector de pesos normalizado."""
        weights = np.random.dirichlet(np.ones(len(self.strategies)))
        return weights

    def _mutate(self, individual):
        """Aplica mutaciones gaussianas a pesos y renormaliza."""
        for i in range(len(individual)):
            if random.random() < self.mutation_rate:
                individual[i] += np.random.normal(0, 0.05)
        individual = np.abs(individual)
        return individual / individual.sum()

    def _crossover(self, parent1, parent2):
        """Combina dos vectores de pesos en un punto de cruce."""
        point = random.randint(1, len(parent1)-1)
        child = np.concatenate([parent1[:point], parent2[point:]])
        return child / child.sum()

    def _evaluate(self, weights):
        """
        Evalúa la rentabilidad esperada de un vector de pesos sobre señales históricas.
        Fitness = dot(weights, net_gains) donde net_gains se calcula de signals.
        """
        df = self.db.load_signals()
        if df.empty:
            return -np.inf
        # Mapear estrategias a índices para Numba
        strat_to_idx = {s: i for i, s in enumerate(self.strategies)}
        ids = np.array([strat_to_idx[s] for s in df['strategy']], dtype=np.int64)
        results = np.array([1 if r == 'WIN' else 0 for r in df['resultado']], dtype=np.int64)
        payouts = np.full(len(self.strategies), self.payout, dtype=np.float64)
        net_gains = _compute_net_gains(ids, results, payouts, len(self.strategies))
        fitness = np.dot(weights, net_gains)
        return fitness

    def optimize(self):
        """
        Ejecuta el Algoritmo Genético y retorna el mejor vector de pesos.
        """
        population = [self._generate_individual() for _ in range(self.population_size)]
        for gen in range(self.generations):
            fitnesses = [self._evaluate(ind) for ind in population]
            # Selección de mejore individuos
            idx_sorted = np.argsort(fitnesses)[::-1]
            survivors = [population[i] for i in idx_sorted[:self.population_size//2]]
            # Reproducción
            children = []
            while len(children) < self.population_size//2:
                p1, p2 = random.sample(survivors, 2)
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                children.append(child)
            population = survivors + children
            print(f"[GA] Generación {gen+1}/{self.generations}, mejor fitness = {fitnesses[idx_sorted[0]]:.2f}")
        best_weights = population[0]
        os.makedirs('ga_results', exist_ok=True)
        np.save('ga_results/best_weights.npy', best_weights)
        print(f"[GA] Optimización finalizada. Best fitness = {self._evaluate(best_weights):.2f}")
        return best_weights


