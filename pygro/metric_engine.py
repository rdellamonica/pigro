from sympy import *
import numpy as np
import json

#########################################################################################
#                               METRIC OBJECT                                           #
#                                                                                       #
#   The metric object contains the symbolic expresison of a generic metric tensor       #
#   and symbolically retrieves the inverse metric and all is needed to compute the      #
#   Christhoffel symbols.                                                               #
#   Its main contents are:                                                              #
#    -  g: the metrics tensor symbolic expression;                                      #
#    -  g_inv: the inverse metrics;                                                     #
#    -  x: an array of coordinates;                                                     #
#    -  u: an array of derivatives of x w.r.t. to the affine parameter;                 #
#                                                                                       #   
#   g and x are user inputs.                                                            #
#                                                                                       #
#########################################################################################

class metric():

    def __init__(self):
        self.initialized = 0
        self.geodesic_engine_linked = False
    
    def initialize_metric(self):
        self.name = input("Insert the name of the spacetime (e.g. 'Kerr metric'): ")

        print("Initialazing {}".format(self.name))
        
        print("Define coordinates symbols:")
        self.x = []
        self.dx = []
        self.x_str = []
        self.u = []
        for i in range(4):
            coordinate = input("Coordinate {}: ".format(i))
            setattr(self, coordinate, symbols(coordinate))
            self.x.append(self.__dict__[coordinate])
            self.x_str.append(coordinate)

            velocity = "u_" + coordinate
            setattr(self, velocity, symbols(velocity))
            self.u.append(self.__dict__[velocity])

            differential = "d" + coordinate
            setattr(self, differential, symbols(differential))
            self.dx.append(self.__dict__[differential])
        

        case = input("From? [tensor/line element]: ")

        if case == "tensor":
            print("Define metric tensor components:")
            self.g = zeros(4, 4)
            self.g_str = np.zeros([4,4], dtype = object)

            for i in range(4):
                for j in range(4):
                    component = input("g[{},{}]: ".format(i, j))
                    self.g[i,j] = parse_expr(component)
                    self.g_str[i,j] = component
        elif case == "line element":
            self.g = zeros(4, 4)
            self.g_str = np.zeros([4,4], dtype = object)
            ds2_str = input("ds^2 = ")
            self.ds2 = parse_expr(ds2_str)
            for i, dx1 in enumerate(self.dx):
                for j, dx2 in enumerate(self.dx):
                    self.g[i,j] = self.ds2.coeff(dx1*dx2,1)
                    self.g_str[i,j] = str(self.g[i,j])
        else:
            raise("Only 'tensor' or 'line element' are accepted method for parsing the metric.")
        
        print("Calculating inverse metric...")
        self.g_inv = self.g.inv()

        self.g_inv_str = np.zeros([4,4], dtype = object)
        
        for i in range(4):
            for j in range(4):
                self.g_inv_str[i,j] = str(self.g_inv[i,j])
        
        print("Calculating symbolic equations of motion:")
        self.eq_u = []
        self.eq_u_str = np.zeros(4, dtype = object)

        self.eq_x = []
        self.eq_x_str = np.zeros(4, dtype = object)

        for rho in range(4):
            print("- {}/4".format(rho+1))
            eq = 0
            for mu in range(4):
                for nu in range(4):
                    eq += -self.chr(mu, nu, rho)*self.u[mu]*self.u[nu]
            self.eq_u.append(eq)
            self.eq_u_str[rho] = str(eq)

            self.eq_x.append(self.u[rho])
            self.eq_x_str[rho] = str(self.u[rho])


        print("Adding to class a method to get initial u_0...")

        eq = 0

        for mu in range(4):
            for nu in range(4):
                eq += self.g[mu, nu]*self.u[mu]*self.u[nu]

        self.u0_s_null = solve(eq, self.u[0], simplify=False, rational=False)[0]

        eq += 1

        self.u0_s_timelike = solve(eq, self.u[0], simplify=False, rational=False)[0]

        self.initialized = 1
        self.constants = {}
        self.transform_functions = []

        free_sym = list(self.g.free_symbols-set(self.x))

        if len(free_sym) > 0:
            for sym in free_sym:
                self.add_constant(str(sym))
                value = float(input("Insert value for {}: ".format(str(sym))))
                self.set_constant(**{str(sym): value})

        self.g_f = lambdify([self.x], self.evaluate_constants(self.g), 'numpy')
        self.g_inv_f = lambdify([self.x], self.evaluate_constants(self.g_inv), 'numpy')

        print("The metric_engine has been initialized.")

    def save_metric(self, filename):
        if self.initialized:
            with open(filename, "w+") as f:
                output = {}
                
                output['name'] = self.name
                output['g'] = self.g_str.tolist()
                output['x'] = self.x_str
                output['g_inv'] = self.g_inv_str.tolist()
                output['eq_x'] = self.eq_x_str.tolist()
                output['eq_u'] = self.eq_u_str.tolist()
                output['u0_timelike'] = str(self.u0_s_timelike)
                output['u0_null'] = str(self.u0_s_null)
                
                if(self.transform_functions):
                    output['transform'] = self.self.transform_functions_str

                json.dump(output, f)

        else:
            print("Inizialize (initialize_metric) or load (load_metric) a metric before saving.")
    
    def load_metric(self, filename, verbose = True, **params):

        f = open(filename, "r")

        load = json.load(f)

        self.name = load['name']

        if verbose:
            print("Loading {}".format(self.name))
        
        self.x = []
        self.x_str = []
        self.u = []

        for i in range(4):

            coordinate = load['x'][i]
            setattr(self, coordinate, symbols(coordinate))
            self.x.append(self.__dict__[coordinate])
            self.x_str.append(coordinate)

            velocity = "u" + coordinate
            setattr(self, velocity, symbols(velocity))
            self.u.append(self.__dict__[velocity])
        
        self.g = zeros(4, 4)
        self.g_inv = zeros(4, 4)
        self.eq_u = []
        self.eq_x = []
        
        self.g_str = np.zeros([4,4], dtype = object)
        self.g_inv_str = np.zeros([4,4], dtype = object)
        self.eq_u_str = np.zeros(4, dtype = object)
        self.eq_x_str = np.zeros(4, dtype = object)

        for i in range(4):

            for j in range(4):

                component = load['g'][i][j]
                self.g[i,j] = parse_expr(component)
                self.g_str[i,j] = component
                component = load['g_inv'][i][j]
                self.g_inv[i,j] = parse_expr(component)
                self.g_inv_str[i,j] = component

            self.eq_u.append(parse_expr(load['eq_u'][i]))
            self.eq_x.append(parse_expr(load['eq_x'][i]))
            self.eq_u_str[i] = load['eq_u'][i]
            self.eq_x_str[i] = load['eq_x'][i]
        
        self.u0_s_null = parse_expr(load['u0_null'])
        self.u0_s_timelike = parse_expr(load['u0_timelike'])
        
        self.initialized = 1
        self.constants = {}

        free_sym = list(self.g.free_symbols-set(self.x))

        if(len(free_sym)) > 0:
            for sym in free_sym:
                self.add_constant(str(sym))
                if str(sym) in params:
                    self.set_constant(**{str(sym): params.get(str(sym))})
                else:
                    self.set_constant(**{str(sym): params.get(str(sym))})

        self.transform_functions = []
        
        '''
        if load['transform']:
            for i in range(3):
                transf = load['transform'][i]
                transform_function = parse_expr(transf)
                self.transform_functions.append(lambdify([self.x[1], self.x[2], self.x[3]], self.evaluate_constants(transform_function), 'numpy'))
        '''

        self.g_f = lambdify([self.x], self.evaluate_constants(self.g), 'numpy')
        self.g_inv_f = lambdify([self.x], self.evaluate_constants(self.g_inv), 'numpy')
        
        if verbose:
            print("The metric_engine has been initialized.")

    def load_metric_from_json(self, metric_json, verbose = True, **params):

        load = metric_json

        self.name = load['name']

        if verbose:
            print("Loading {}".format(self.name))
        
        self.x = []
        self.x_str = []
        self.u = []

        for i in range(4):

            coordinate = load['x'][i]
            setattr(self, coordinate, symbols(coordinate))
            self.x.append(self.__dict__[coordinate])
            self.x_str.append(coordinate)

            velocity = "u" + coordinate
            setattr(self, velocity, symbols(velocity))
            self.u.append(self.__dict__[velocity])
        
        self.g = zeros(4, 4)
        self.g_inv = zeros(4, 4)
        self.eq_u = []
        self.eq_x = []
        
        self.g_str = np.zeros([4,4], dtype = object)
        self.g_inv_str = np.zeros([4,4], dtype = object)
        self.eq_u_str = np.zeros(4, dtype = object)
        self.eq_x_str = np.zeros(4, dtype = object)

        for i in range(4):

            for j in range(4):

                component = load['g'][i][j]
                self.g[i,j] = parse_expr(component)
                self.g_str[i,j] = component
                component = load['g_inv'][i][j]
                self.g_inv[i,j] = parse_expr(component)
                self.g_inv_str[i,j] = component

            self.eq_u.append(parse_expr(load['eq_u'][i]))
            self.eq_x.append(parse_expr(load['eq_x'][i]))
            self.eq_u_str[i] = load['eq_u'][i]
            self.eq_x_str[i] = load['eq_x'][i]
        
        self.u0_s_null = parse_expr(load['u0_null'])
        self.u0_s_timelike = parse_expr(load['u0_timelike'])
        
        self.initialized = 1
        self.constants = {}

        free_sym = list(self.g.free_symbols-set(self.x))

        if(len(free_sym)) > 0:
            for sym in free_sym:
                self.add_constant(str(sym))
                if str(sym) in params:
                    self.set_constant(**{str(sym): params.get(str(sym))})
                else:
                    self.set_constant(**{str(sym): params.get(str(sym))})

        self.transform_functions = []
        
        '''
        if load['transform']:
            for i in range(3):
                transf = load['transform'][i]
                transform_function = parse_expr(transf)
                self.transform_functions.append(lambdify([self.x[1], self.x[2], self.x[3]], self.evaluate_constants(transform_function), 'numpy'))
        '''

        self.g_f = lambdify([self.x], self.evaluate_constants(self.g), 'numpy')
        self.g_inv_f = lambdify([self.x], self.evaluate_constants(self.g_inv), 'numpy')
        
        if verbose:
            print("The metric_engine has been initialized.")

    def add_constant(self, symbol):
        if self.initialized:
            self.constants[symbol] = {}
            self.constants[symbol]['symbol'] = symbol
            self.constants[symbol]['value'] = None
        else:
            print("Inizialize (initialize_metric) or load (load_metric) a metric before adding constants.")
    
    def set_constant(self, **params):
        if self.initialized:
            for param in params:
                try:
                    self.constants[str(param)]['value'] = params[param]
                except:
                    print(f"No constant named '{symbol}' in the metric_engine.")
                    break
            self.g_f = lambdify([self.x], self.evaluate_constants(self.g), 'numpy')
            if self.geodesic_engine_linked:
                self.geodesic_engine.evaluate_constants()
        else:
            print("Inizialize (initialize_metric) or load (load_metric) a metric before adding constants.")

    def evaluate_constants(self, expr):
        if any(x['value'] == None for x in self.constants.values()):
            print("You must set_constant for every constant value in your metric, before evaluating.")
        else:
            subs = []
            for c in self.constants.values():
                x = c['symbol']
                y = c['value']
                subs.append([x,y])
            return expr.subs(subs)
    
    def chr(self, mu, nu, rho):
        ch = 0
        for sigma in range(4):
            ch += self.g_inv[rho,sigma]*(self.g[sigma, nu].diff(self.x[mu])+self.g[mu, sigma].diff(self.x[nu])-self.g[mu, nu].diff(self.x[sigma]))/2
        return ch

    def set_coordinate_transformation(self):
        print("Define tranforamtion to pseudo-cartesian coordinates (useful for plotting):")
        self.transform_functions = []
        self.transform_functions_str = []
        coords = ["x", "y", "z"]
        for i in range(3):
            transf = input("{} = ".format(coords[i]))
            transform_function = parse_expr(transf)
            self.transform_functions_str.append(transf)
            self.transform_functions.append(lambdify([self.x[1], self.x[2], self.x[3]], self.evaluate_constants(transform_function), 'numpy'))

    def transform(self, X):
        return self.transform_functions[0](X[0], X[1], X[2]), self.transform_functions[1](X[0], X[1], X[2]), self.transform_functions[2](X[0], X[1], X[2])

    def norm4(self, x, v):
        norm = 0
        
        for mu in range(4):
            for nu in range(4):
                norm += self.g_f(x)[mu, nu]*v[mu]*v[nu]
        
        return norm

    def set_constant_of_motion(self, name, expr):
        self.constants_of_motion[name] = lambdify([self.x, self.u], self.evaluate_constants(expr), 'numpy')