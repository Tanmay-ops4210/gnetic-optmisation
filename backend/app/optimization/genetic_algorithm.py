import random
import numpy as np
from typing import Dict, Any, List, Tuple, Callable, Optional
from dataclasses import dataclass, field
import copy

@dataclass
class Individual:
    params: Dict[str, Any]
    fitness: float = 0.0
    model_name: str = ''

def _random_value(space_def: Tuple) -> Any:
    lo, hi, typ = space_def
    if typ == 'int':
        return random.randint(int(lo), int(hi))
    elif typ == 'float':
        return round(random.uniform(float(lo), float(hi)), 4)
    elif typ == 'choice':
        return random.choice(lo)  # lo is list of choices here
    return lo

def _init_individual(ga_space: Dict) -> Dict[str, Any]:
    return {k: _random_value(v) for k, v in ga_space.items()}

def _clamp(val, lo, hi, typ):
    if typ == 'int':
        return max(int(lo), min(int(hi), int(round(val))))
    elif typ == 'float':
        return max(float(lo), min(float(hi), float(val)))
    return val

def _crossover(p1: Dict, p2: Dict, ga_space: Dict, rate: float) -> Tuple[Dict, Dict]:
    c1, c2 = copy.deepcopy(p1), copy.deepcopy(p2)
    for k in ga_space:
        if random.random() < rate:
            c1[k], c2[k] = c2[k], c1[k]
    return c1, c2

def _mutate(individual: Dict, ga_space: Dict, rate: float) -> Dict:
    ind = copy.deepcopy(individual)
    for k, space_def in ga_space.items():
        if random.random() < rate:
            ind[k] = _random_value(space_def)
    return ind

def _tournament_select(population: List[Individual], k: int = 3) -> Individual:
    candidates = random.sample(population, min(k, len(population)))
    return max(candidates, key=lambda x: x.fitness)

def _roulette_select(population: List[Individual]) -> Individual:
    total = sum(max(ind.fitness, 0) for ind in population)
    if total == 0:
        return random.choice(population)
    r = random.uniform(0, total)
    cumulative = 0.0
    for ind in population:
        cumulative += max(ind.fitness, 0)
        if cumulative >= r:
            return ind
    return population[-1]


class GeneticAlgorithm:
    def __init__(
        self,
        population_size: int,
        generations: int,
        mutation_rate: float,
        crossover_rate: float,
        selection_method: str,
        fitness_fn: Callable[[str, Dict], float],
        model_names: List[str],
        model_registry: Dict,
        callback: Optional[Callable] = None,
        stop_flag: Optional[list] = None,  # [False] — set to [True] to stop
    ):
        self.pop_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.selection_method = selection_method
        self.fitness_fn = fitness_fn
        self.model_names = model_names
        self.model_registry = model_registry
        self.callback = callback
        self.stop_flag = stop_flag or [False]
        self.best_individual: Optional[Individual] = None
        self.fitness_history: List[Dict] = []
        self.all_evaluated: List[Dict] = []

    def _init_population(self) -> List[Individual]:
        pop = []
        for _ in range(self.pop_size):
            model_name = random.choice(self.model_names)
            ga_space = self.model_registry[model_name]['ga_space']
            params = _init_individual(ga_space)
            pop.append(Individual(params=params, model_name=model_name))
        return pop

    def _evaluate(self, individual: Individual) -> float:
        try:
            score = self.fitness_fn(individual.model_name, individual.params)
            return max(0.0, score)
        except Exception:
            return 0.0

    def _select(self, population: List[Individual]) -> Individual:
        if self.selection_method == 'roulette':
            return _roulette_select(population)
        return _tournament_select(population)

    def run(self):
        population = self._init_population()
        
        # Evaluate initial population
        for ind in population:
            if self.stop_flag[0]:
                break
            ind.fitness = self._evaluate(ind)
            self.all_evaluated.append({
                'model': ind.model_name,
                'params': ind.params,
                'score': ind.fitness,
            })
        
        if not population:
            return
        
        self.best_individual = max(population, key=lambda x: x.fitness)
        
        for gen in range(self.generations):
            if self.stop_flag[0]:
                break
            
            new_population = []
            
            # Elitism: keep best 2
            sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
            new_population.extend([copy.deepcopy(sorted_pop[0]), copy.deepcopy(sorted_pop[1])])
            
            while len(new_population) < self.pop_size:
                if self.stop_flag[0]:
                    break
                
                p1 = self._select(population)
                p2 = self._select(population)
                
                # Crossover — same model for simplicity, or random
                if random.random() < self.crossover_rate and p1.model_name == p2.model_name:
                    ga_space = self.model_registry[p1.model_name]['ga_space']
                    c1_params, c2_params = _crossover(p1.params, p2.params, ga_space, 0.5)
                else:
                    c1_params = copy.deepcopy(p1.params)
                    c2_params = copy.deepcopy(p2.params)
                    # Possibly switch model
                    c2_model = random.choice(self.model_names)
                    ga_space2 = self.model_registry[c2_model]['ga_space']
                    c2_params = _init_individual(ga_space2)
                    
                    child2 = Individual(
                        params=_mutate(c2_params, ga_space2, self.mutation_rate),
                        model_name=c2_model
                    )
                    child2.fitness = self._evaluate(child2)
                    self.all_evaluated.append({
                        'model': child2.model_name,
                        'params': child2.params,
                        'score': child2.fitness,
                    })
                    new_population.append(child2)
                    
                    ga_space1 = self.model_registry[p1.model_name]['ga_space']
                    child1 = Individual(
                        params=_mutate(c1_params, ga_space1, self.mutation_rate),
                        model_name=p1.model_name
                    )
                    child1.fitness = self._evaluate(child1)
                    self.all_evaluated.append({
                        'model': child1.model_name,
                        'params': child1.params,
                        'score': child1.fitness,
                    })
                    new_population.append(child1)
                    continue
                
                ga_space1 = self.model_registry[p1.model_name]['ga_space']
                child1 = Individual(
                    params=_mutate(c1_params, ga_space1, self.mutation_rate),
                    model_name=p1.model_name
                )
                child1.fitness = self._evaluate(child1)
                self.all_evaluated.append({
                    'model': child1.model_name,
                    'params': child1.params,
                    'score': child1.fitness,
                })
                new_population.append(child1)
                
                if len(new_population) < self.pop_size:
                    ga_space2 = self.model_registry[p2.model_name]['ga_space']
                    child2 = Individual(
                        params=_mutate(c2_params, ga_space2, self.mutation_rate),
                        model_name=p2.model_name
                    )
                    child2.fitness = self._evaluate(child2)
                    self.all_evaluated.append({
                        'model': child2.model_name,
                        'params': child2.params,
                        'score': child2.fitness,
                    })
                    new_population.append(child2)
            
            population = new_population[:self.pop_size]
            
            gen_best = max(population, key=lambda x: x.fitness)
            if gen_best.fitness > self.best_individual.fitness:
                self.best_individual = copy.deepcopy(gen_best)
            
            avg_fitness = float(np.mean([ind.fitness for ind in population]))
            self.fitness_history.append({
                'generation': gen + 1,
                'best': round(self.best_individual.fitness, 6),
                'avg': round(avg_fitness, 6),
            })
            
            if self.callback:
                self.callback(gen + 1, self.best_individual, avg_fitness, population)
        
        return self.best_individual
