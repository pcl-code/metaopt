# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function

from numpy.random import randn
from random import sample, gauss
from math import exp

from orges.args import ArgsCreator

class SAESOptimizer(object):
    MU = 10
    LAMBDA = 10
    TAU0 = 0.5
    TAU1 = 0.5

    def __init__(self, invoker):
        self.invoker = invoker
        self.invoker.caller = self

        self.population = []
        self.scored_population = []
        self.best_scored_indivual = (None, None)

        self.generation = 1


    def initalize_population(self):
        # TODO implement me
        pass


    def optimize(self, f, param_spec, return_spec=None, minimize=True):
        self.f = f
        self.param_spec = param_spec

        self.initalize_population()
        self.score_population()

        while not self.exit_condition():
            self.add_offspring()
            self.score_population()
            self.select_parents()

            print(self.best_scored_indivual[0])
            self.generation += 1

        return self.best_scored_indivual[0]

    def exit_condition(self):
        pass

    def initalize_population(self):
        args_creator = ArgsCreator(self.param_spec)

        for _ in xrange(SAESOptimizer.MU):
            args = args_creator.random()
            args_sigma = list(randn(len(args)))

            individual = (args, args_sigma)
            self.population.append(individual)

    def add_offspring(self):
        args_creator = ArgsCreator(self.param_spec)

        for _ in xrange(SAESOptimizer.LAMBDA):
            mother, father = sample(self.population, 2)

            child_args = args_creator.combine(mother[0], father[0])

            mean = lambda x1,x2: (x1 + x2) / 2
            child_args_sigma = map(mean, mother[1], father[1])

            child_args = args_creator.randomize(child_args, child_args_sigma)

            tau0_random = gauss(0, 1)

            def mutate_sigma(sigma):
                tau0 = SAESOptimizer.TAU0
                tau1 = SAESOptimizer.TAU1
                return sigma * exp(tau0 * tau0_random)\
                       * exp(tau1 * gauss(0, 1))

            child_args_sigma = map(mutate_sigma, child_args_sigma)

            child = (child_args, child_args_sigma)

            self.population.append(child)


    def score_population(self):
        for individual in self.population:
            args, _ = individual
            self.invoker.invoke(self.f, args, individual)

        self.invoker.wait()

    def select_parents(self):
        self.scored_population.sort(key=lambda s: s[1])
        new_scored_population = self.scored_population[0:SAESOptimizer.MU]
        self.population = map(lambda s: s[0], new_scored_population)

    def on_result(self, args, result, individual):
        # _, fitness = result
        fitness = result
        scored_individual = (individual, fitness)
        self.scored_population.append(scored_individual)

        best_individual, best_fitness = self.best_scored_indivual

        if best_fitness is None or fitness < best_fitness:
            self.best_scored_indivual = scored_individual

    def on_error(self, args, error, individual):
        pass

if __name__ == '__main__':
    from orges.invoker.simpleinvoker import SimpleInvoker
    from orges.paramspec import ParamSpec
    from orges.demo.algorithm.host.saes import f as saes

    def f(args):
        args["d"] = 2
        args["epsilon"] = 0.0001
        args["mu"] = 100
        args["lambd"] = 100
        return saes(args)

    param_spec = ParamSpec()

    param_spec.float("tau0", "τ1").interval((0, 1)).step(0.1)
    param_spec.float("tau1", "τ2").interval((0, 1)).step(0.1)

    invoker = SimpleInvoker()

    optimizer = SAESOptimizer(invoker)
    optimizer.optimize(f, param_spec)