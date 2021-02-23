from src.enums import ModelResolveMethod
from src.local_optimization_result import LocalOptimizationResult
from src.pod import Pod
import multiprocess as mp
import matplotlib.pyplot as plt
import numpy as np

# from src.aggr_solver import Solver
from src.aggregator_solver import Solver


def worker(arg):
    obj = arg
    return obj.resolve()


class Aggregator(object):

    def __init__(self, pods=None):
        if pods is None:
            self.pods = []
        else:
            self.set_pods(pods)
        # self.solver = None
        self.resolve_method = None
        self.local_optimization_result = None
        self.input = {
            'baseline': [0] * 96,
            'maximized': {
                'flexibilities': []  # TODO: change 96 to timestamps
            },
            'minimized': {
                'flexibilities': []  # TODO: change 96 to timestamps
            },
            'costs': {
                'buy': np.load('Prices_test/buyTest.npy').tolist(),
                # [10 if i < (96 / 2) else 13 for i in range(96)], #
                'sell': np.load('Prices_test/sellTest.npy').tolist(),
                # [12 if i < (96 / 4) * 3 else 9 for i in range(96)], #
                'production': np.load('Prices_test/prodTest.npy').tolist(),
                # [3 if i < (96 / 4) else 11 for i in range(96)] #
            }
        }
        self.result = {
            'date': None,
            'optimizations': None
        }

    def __init_input(self):
        if self.local_optimization_result is None:
            self.local_optimization_result = LocalOptimizationResult()

            self.local_optimization_result.populate(self.pods)

        try:
            for el in self.local_optimization_result.get_optimizations():
                self.input['maximized']['flexibilities'].append(el['maximized']['flexibility'])
                self.input['minimized']['flexibilities'].append(el['minimized']['flexibility'])
                self.input['baseline'] = [x + y for x, y in zip(self.input['baseline'], el['baseline'])]

                # Testing..
                # self.input['maximized']['flexibilities'].append([20 if i < (96 / 2) else 20 for i in range(96)])
                # self.input['minimized']['flexibilities'].append([10 if i < (96 / 2) else -10 for i in range(96)])
                # self.input['baseline'] = [15 if i < (96 / 4) * 3 else 15 for i in range(96)]

            self.__fix_flexibility_bounds()
            self.__fix_baseline()

        except:
            raise Exception('LocalOptimizationResult not correctly set.')

    # Minimized Flexibility value cannot exceed Maximized Flexibility value
    def __fix_flexibility_bounds(self):
        for i in range(0, len(self.input['maximized']['flexibilities'])):
            self.input['maximized']['flexibilities'][i] = [x if x > y else y for x, y in
                                                           zip(self.input['minimized']['flexibilities'][i],
                                                               self.input['maximized']['flexibilities'][i])]

    # Baseline value cannot exceed Flexibility bounds (misscalculated because SimpleStorage has no baseline)
    def __fix_baseline(self):
        sum_max = [sum(col) for col in zip(*self.input['maximized']['flexibilities'])]
        sum_min = [sum(col) for col in zip(*self.input['minimized']['flexibilities'])]

        self.input['baseline'] = [i if b > i else b for i, b in zip(sum_max, self.input['baseline'])]
        self.input['baseline'] = [i if b < i else b for i, b in zip(sum_min, self.input['baseline'])]
        # self.plot_results(sum_max, sum_min, self.input['baseline'])

    def add_pod(self, pod):
        if isinstance(pod, Pod):
            self.pods.append(pod)
        else:
            raise Exception('{} passed argument is not of type Pod'.format(pod))

    def set_pods(self, pods: [Pod]):
        try:
            for p in pods:
                self.add_pod(p)
        except:
            raise Exception('pods is not iterable')

    def set_local_optimization_result(self, opt: LocalOptimizationResult):
        if isinstance(opt, LocalOptimizationResult):
            self.local_optimization_result = opt
        else:
            raise Exception('{} passed argument is not of type LocalOptimizationResult'.format(LocalOptimizationResult))

    # SIMPLE RESOLVE METHODS
    def resolve_pods(self):
        for pod in self.pods:
            if pod.needs_local_optimization():
                pod.resolve()

    def resolve_pods_multiprocessing(self):
        n_core = mp.cpu_count()  # set to the number of cores you want to use
        try:
            with mp.Pool(n_core) as pool:
                self.pods = pool.map(worker, self.pods)
        except TimeoutError:
            "We lacked patience and got a multiprocessing.TimeoutError"

    # RESOLVE AND AGGREGATE METHODS
    def resolve_pods_and_aggregate(self):
        for pod in self.pods:
            if pod.needs_local_optimization():
                pod.resolve()
        return self.aggregate()

    # AGGREGATE METHODS

    # New Aggregator -  optimization model
    def aggregate(self, model_resolve_method=ModelResolveMethod.MAXIMIZE, print_results=True,
                  print_graphs=False, tee=False, pprint=False, per_allegra=False):

        self.__init_input()
        self.resolve_method = model_resolve_method
        self.solver = None
        self.solver = Solver(self.input)

        self.solver.resolve(model_resolve_method, print_results, tee, pprint)

        self.result['date'] = self.local_optimization_result.data['date']
        self.result['optimizations'] = self.solver.results

        if print_graphs:
            if model_resolve_method == ModelResolveMethod.MINIMIZE:
                self.print_graph('minimized')
            elif model_resolve_method == ModelResolveMethod.MAXIMIZE:
                self.print_graph('maximized')
            elif model_resolve_method == ModelResolveMethod.MINIMIZE_AND_MAXIMIZE:
                self.print_graph('minimized')
                self.print_graph('maximized')
                self.print_graph_2()

        if per_allegra:
            self.graphs_for_allegra()

        return self.result

    def print_graph(self, method):
        fig, ax = plt.subplots(figsize=(20, 15))
        ax.set(xlabel='Timestamp (t)', ylabel='Active Power (W)',
               title='Model Results - {} - {}'.format(method, self.solver.results[method]['solution_value']))
        plt.xticks(range(0, 96, 5))
        ax.plot(self.solver.results[method]['MAX_F'], label='MAX_Flex')
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        plt.show()

    def plot_results(self, max, min, baseline):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set(xlabel='Time', ylabel='Active Power (W)', title='Aggregated Flexibility Results')
        plt.xticks(range(0, 96, 5))

        ax.plot(max, label='MAX')
        ax.plot(min, label='MIN')

        ax.plot(baseline, label='baseline')
        plt.legend(bbox_to_anchor=(1, 1), loc=1, borderaxespad=0.3)
        plt.show()
