import pyomo.environ as pyo
import numpy as np
import copy
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.core import Var, Objective
import matplotlib.pyplot as plt
import seaborn as sns

from src.enums import ModelResolveMethod
from src.pod_model import Model
from src.profile import Profile

sns.set()


class Solver:

    def __init__(self, data):
        self.data = data
        self.data_for_instance = self.__init_data()
        result_var = {
            'grid': [0 for _ in range(self.data['n_timestamps'])],
            'pv_shift': [[0 for _ in range(self.data['n_timestamps'])] for _ in range(self.data['n_pv'])],
            'load_t2_shift': [[0 for _ in range(self.data['n_timestamps'])] for _ in range(self.data['n_load_t2'])],
            'load_t3_shift': [[0 for _ in range(self.data['n_timestamps'])] for _ in range(self.data['n_load_t3'])],
            'chp_shift': [[0 for _ in range(self.data['n_timestamps'])] for _ in range(self.data['n_chp'])],
            'storage_charge': [0 for _ in range(self.data['n_timestamps'])],
            'solution_value': None  # For the solution value
        }
        self.results = {
            'minimized': copy.deepcopy(result_var),
            'maximized': copy.deepcopy(result_var)
        }
        self.model = Model(data['storage'])

    def __init_data(self):
        result = {None: {}}
        for key, value in self.data.items():
            result[None][key] = {None: value}
        return result

    def add_profile(self, profile: Profile):
        self.__profiles.append(profile)

    def set_profiles(self, profiles: [Profile]):
        self.__profiles = profiles

    def add_data_field(self, field_name, data):
        if isinstance(data, list):
            if len(data) < 1:
                raise Exception('{} data with no length'.format(field_name))
            else:
                if isinstance(data[0], (list, np.ndarray)):
                    self.add_multidimension_array_data_field(field_name, data, len(data[0]))
                else:
                    self.add_array_data_field(field_name, data)
        else:
            self.add_single_field(field_name, data)

    def add_single_field(self, field_name, value):
        self.data_for_instance[None][field_name] = {None: value}

    def add_array_data_field(self, field_name, data):
        self.data_for_instance[None][field_name] = {}
        for i in range(len(data)):
            self.data_for_instance[None][field_name][i] = data[i]

    def add_multidimension_array_data_field(self, field_name, data, nested_dimension):
        self.data_for_instance[None][field_name] = {}
        for i in range(len(data)):
            for j in range(nested_dimension):
                self.data_for_instance[None][field_name][(i, j)] = data[i][j]

    def resolve(self, model_resolve_method: ModelResolveMethod, tee=True, pprint=False):

        instance = self.model.create_instance(self.data_for_instance)

        if model_resolve_method == ModelResolveMethod.MINIMIZE:

            instance.objective_function_minimize.activate()
            instance.objective_function_maximize.deactivate()
            self.__resolve_model_and_results('minimized', instance, tee, pprint)

        elif model_resolve_method == ModelResolveMethod.MAXIMIZE:

            instance.objective_function_minimize.deactivate()
            instance.objective_function_maximize.activate()
            self.__resolve_model_and_results('maximized', instance, tee, pprint)

        elif model_resolve_method == ModelResolveMethod.MINIMIZE_AND_MAXIMIZE:
            instance.objective_function_minimize.activate()
            instance.objective_function_maximize.deactivate()
            self.__resolve_model_and_results('minimized', instance, False, False)
            instance.objective_function_minimize.deactivate()
            instance.objective_function_maximize.activate()
            self.__resolve_model_and_results('maximized', instance, False, False)
            self.print_graph()

    def __resolve_model_and_results(self, model_resolve_method, instance, tee, pprint):
        solver = pyo.SolverFactory('gurobi', solver_io="python")
        result = solver.solve(instance, tee=tee)

        if pprint:
            instance.pprint()

        # Check the results and extract the values if the solution is optimal
        if (result.solver.status == SolverStatus.ok) and (
                result.solver.termination_condition == TerminationCondition.optimal):

            # instance.pprint()

            for v in instance.component_objects(Var, active=True):
                # print ("Variable",v)
                varobject = getattr(instance, str(v))
                if v.name == 'grid':
                    for index in varobject:
                        self.results[model_resolve_method]['grid'][index] = varobject[index].value
                if v.name == 'pv_shift':
                    for index in varobject:
                        self.results[model_resolve_method]['pv_shift'][index[0]][index[1]] = varobject[index].value
                if v.name == 'load_t2_shift':
                    for index in varobject:
                        self.results[model_resolve_method]['load_t2_shift'][index[0]][index[1]] = varobject[index].value
                if v.name == 'load_t3_shift':
                    for index in varobject:
                        self.results[model_resolve_method]['load_t3_shift'][index[0]][index[1]] = varobject[index].value
                if v.name == 'chp_shift':
                    for index in varobject:
                        self.results[model_resolve_method]['chp_shift'][index[0]][index[1]] = varobject[index].value
                if v.name == 'storage_charge':
                    for index in varobject:
                        self.results[model_resolve_method]['storage_charge'][index] = varobject[index].value
            for v in instance.component_objects(Objective, active=True):
                self.results[model_resolve_method]['solution_value'] = v.expr()


        elif result.solver.termination_condition == TerminationCondition.infeasible:
            print('############################ INFEASIBLE MODEL ############################')
            raise Exception('############################ INFEASIBLE MODEL ############################')
        else:
            print('############################ SOMETHING WENT WRONG ############################')
            print("Solver Status: ", result.solver.status)
            raise Exception(
                "############################ SOMETHING WENT WRONG ############################\nSolver Status: ",
                result.solver.status)

    def print_graph(self):

        fig, ax = plt.subplots(figsize=(20, 15))
        ax.set(xlabel='Timestamp (t)', ylabel='Active Power (MW)', title='Model Grid Results')
        plt.xticks(range(0, 96, 5))

        ax.plot(self.results['minimized']['grid'], label='Grid (minimized)')
        ax.plot(self.results['maximized']['grid'], label='Grid (maximized)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        plt.show()