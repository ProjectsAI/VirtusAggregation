import pyomo.environ as pyo


class Model:

    def __init__(self):
        self.model = pyo.AbstractModel()
        self.__setup_model()
        self.__setup_vars()
        self.__setup_parameters()
        self.__setup_constraints()
        self.__setup_objective()

    def __setup_model(self):
        # Number of timestamps
        self.model.n_timestamps = pyo.Param(domain=pyo.PositiveIntegers)
        # Number of Pods
        self.model.n_pods = pyo.Param(domain=pyo.PositiveIntegers)

        self.model.T = pyo.RangeSet(0, self.model.n_timestamps - 1)  # 0..95
        self.model.N = pyo.RangeSet(0, self.model.n_pods - 1)  # 0..n - 1

    def __setup_vars(self):
        # useful for plotting
        self.model.BASELINE = pyo.Var(self.model.T, domain=pyo.Reals)

        # Max flexibility
        self.model.MAX_BOUND = pyo.Var(self.model.T, domain=pyo.Reals)

        # Min flexibility
        self.model.MIN_BOUND = pyo.Var(self.model.T, domain=pyo.Reals)

        # Gain
        self.model.G_in = pyo.Var(self.model.T, domain=pyo.Reals)
        self.model.G_out = pyo.Var(self.model.T, domain=pyo.Reals)
        self.model.GAIN_MAX = pyo.Var(self.model.T, domain=pyo.Reals)
        self.model.GAIN_MIN = pyo.Var(self.model.T, domain=pyo.Reals)

    def __setup_parameters(self):
        # Sum of Pod baselines
        self.model.baseline = pyo.Param(self.model.T, domain=pyo.Reals)
        # Max Pod flexibilities
        self.model.pod_max_flex = pyo.Param(self.model.N, self.model.T, domain=pyo.Reals)
        # Min Pod flexibilities
        self.model.pod_min_flex = pyo.Param(self.model.N, self.model.T, domain=pyo.Reals)

        # Costs
        self.model.c_in = pyo.Param(self.model.T, domain=pyo.Reals)
        self.model.c_out = pyo.Param(self.model.T, domain=pyo.Reals)
        self.model.c_p = pyo.Param(self.model.T, domain=pyo.Reals)

        # Cases
        self.model.max_can_buy = pyo.Param(self.model.T, default=0, domain=pyo.Binary, mutable=True)
        self.model.max_can_sell = pyo.Param(self.model.T, default=0, domain=pyo.Binary, mutable=True)
        self.model.min_can_buy = pyo.Param(self.model.T, default=0, domain=pyo.Binary, mutable=True)
        self.model.min_can_sell = pyo.Param(self.model.T, default=0, domain=pyo.Binary, mutable=True)

    def __setup_constraints(self):
        ##############################################################################################
        #
        #   Vars needed for plotting bounds
        #
        ##############################################################################################
        # init BASELINE value
        def baseline_value(m, t):
            return (m.baseline[t], m.BASELINE[t], m.baseline[t])

        self.model.baseline_value = pyo.Constraint(self.model.T, rule=baseline_value)

        ##############################################################################################
        #
        #   MAX_BOUND
        #
        ##############################################################################################
        # MAX_BOUND lb
        def max_bound_lb(m, t):
            return m.MAX_BOUND[t] >= m.baseline[t]

        self.model.max_bound_lb = pyo.Constraint(self.model.T, rule=max_bound_lb)

        # MAX_BOUND ub
        def max_bound_ub(m, t):
            return m.MAX_BOUND[t] <= sum(m.pod_max_flex[n, t] for n in m.N)

        self.model.max_bound_ub = pyo.Constraint(self.model.T, rule=max_bound_ub)

        ##############################################################################################
        #
        #   MIN_BOUND
        #
        ##############################################################################################
        # MIN_BOUND lb
        def min_bound_lb(m, t):
            return m.MIN_BOUND[t] >= sum(m.pod_min_flex[n, t] for n in m.N)

        self.model.min_bound_lb = pyo.Constraint(self.model.T, rule=min_bound_lb)

        # MIN_BOUND ub
        def min_bound_ub(m, t):
            return m.MIN_BOUND[t] <= m.baseline[t]

        self.model.min_bound_ub = pyo.Constraint(self.model.T, rule=min_bound_ub)


        ##############################################################################################
        #
        #   G_in / G_out value
        #
        ##############################################################################################
        # G_in lb
        def G_in_value(m, t):
            return m.G_in[t] == m.c_p[t] - m.c_in[t]

        self.model.G_in_value = pyo.Constraint(self.model.T, rule=G_in_value)

        # G_out ub
        def G_out_value(m, t):
            return m.G_out[t] == m.c_out[t] - m.c_p[t]

        self.model.G_out_value = pyo.Constraint(self.model.T, rule=G_out_value)

        ##############################################################################################
        #
        #   GAIN
        #
        ##############################################################################################
        def GAIN_MAX_rule(m, t):
            return m.GAIN_MAX[t] == (m.G_in[t] * m.max_can_buy[t] - m.G_out[t] * m.max_can_sell[t])

        self.model.GAIN_MAX_rule = pyo.Constraint(self.model.T, rule=GAIN_MAX_rule)

        def GAIN_MIN_rule(m, t):
            return m.GAIN_MIN[t] == (m.G_in[t] * m.min_can_buy[t] - m.G_out[t] * m.min_can_sell[t])

        self.model.GAIN_MIN_rule = pyo.Constraint(self.model.T, rule=GAIN_MIN_rule)

    def __setup_objective(self):
        def objective_function_minimize(m):
            return sum(m.GAIN_MAX[t] * m.MAX_BOUND[t] + m.GAIN_MIN[t] * m.MIN_BOUND[t] for t in m.T)

        self.model.objective_function_minimize = pyo.Objective(sense=pyo.minimize, rule=objective_function_minimize)

        def objective_function_maximize(m):
            return sum(m.GAIN_MAX[t] * (m.MAX_BOUND[t]) + m.GAIN_MIN[t] * (m.MIN_BOUND[t]) for t in m.T)

        self.model.objective_function_maximize = pyo.Objective(sense=pyo.maximize, rule=objective_function_maximize)

    def create_instance(self, data):
        return self.model.create_instance(data)
