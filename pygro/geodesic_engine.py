import numpy as np
import time
import sympy as sp
import pygro.integrators as integrators

#########################################################################################
#                               GEODESIC ENGINE                                         #
#                                                                                       #
#   This is the main engine for numerical integration of the geodesic equation.         #
#   Two classes are defined:                                                            #
#    - The integration engine itself, which is linked to a metric object and            #
#      retrieves the equation of motion symbolically.                                   #
#    - The geodesic object, in which the numerical integration result is stored         #
#                                                                                       #
#########################################################################################


################################################################
#   The geodesic_engine object needs as argument               #
#    a metric object which is linked to the metric             #
################################################################


<<<<<<< HEAD
class GeodesicEngine():
=======
class GeodesicEngine(object):
>>>>>>> develop

    def __init__(self, metric, verbose = True):

        self.link_metrics(metric, verbose)
    
    def link_metrics(self, g, verbose):
        if verbose:
            print("Linking {} to the Geodesic Engine".format(g.name))

        self.metric = g
        self.eq_x = g.eq_x
        self.eq_u = g.eq_u
        
        self.u0_s_null = g.u0_s_null
        self.u0_s_timelike = g.u0_s_timelike

        self.metric.geodesic_engine_linked = True
        self.metric.geodesic_engine = self

        self.evaluate_constants()

        if verbose:
            print("Metric linking complete.")

    def stopping_criterion(self, x):
        return True

    def set_stopping_criterion(self, f):
        self.stopping_criterion = f

    def integrate(self, geo, tauf, verbose=False, direction = "fw", **params):
        if verbose:
            print("Integrating...")

        
        integrator = integrators.CashKarp(self.motion_eq, **params)

        if direction == "bw":
            h = -h
            tauf = -tauf

        if verbose:
            time_start = time.perf_counter()

        tau, xu = integrator.integrate(0, tauf, np.array([*geo.initial_x, *geo.initial_u]))
                
        if verbose:
            time_elapsed = (time.perf_counter() - time_start)
            print("Integration time = {} s".format(time_elapsed))

        geo.tau = tau
        geo.x = np.stack(xu[:,:4])
        geo.u = np.stack(xu[:,4:])
    
    def evaluate_constants(self):

        eq_u = []
        for eq in self.eq_u:
            eq_u.append(self.metric.evaluate_constants(eq))

        motion_eq_f = sp.lambdify([*self.metric.x, *self.metric.u], [*self.eq_x, *eq_u], 'numpy')

        def f(tau, xu):
            return np.array(motion_eq_f(*xu))

        self.motion_eq = f
        
        u0_timelike = self.metric.evaluate_constants(self.u0_s_timelike)
        u0_null = self.metric.evaluate_constants(self.u0_s_null)

        self.u0_f_null = sp.lambdify([self.metric.x, self.metric.u[1], self.metric.u[2], self.metric.u[3]], u0_null, 'numpy')
        self.u0_f_timelike = sp.lambdify([self.metric.x, self.metric.u[1], self.metric.u[2], self.metric.u[3]], u0_timelike, 'numpy')