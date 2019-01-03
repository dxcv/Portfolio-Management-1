# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 13:29:22 2018

@author: shaolun du
@contacts: shaolun.du@gmail.com
"""
""" Shared attributes and functions of FD """
import numpy as np

class FiniteDifferences(object):
    """ This object is a prototype of finite difference
        method solving option price
    """
    def __init__(self, S0, K, r,T, sigma, Smax, 
                 M, N, is_call = True ):
        self.S0 = S0
        self.K = K
        self.r = r
        self.T = T
        self.sigma = sigma
        self.Smax = Smax
        self.M, self.N = int(M), int(N)
        self.is_call = is_call
        
        self.dS = Smax/float(self.M)
        self.dt = T/float(self.N)
        self.i_values = np.arange(self.M)
        self.j_values = np.arange(self.N)
        self.grid = np.zeros(shape = (self.M+1, self.N+1))
        self.boundary_conds = np.linspace(0, Smax, self.M+1)
    
    """ Leave ports here 
        Whenever an instance(derived from this class)
        initilize it should implements these ports
    """
    def _setup_coefficients_(self):
        pass
    def _setup_boundary_conditions_(self):
        pass
    def _traverse_grid_(self):
        """ Iterate the grid in times(dt)
        """
        pass
    def _interpolate_(self):
        """ Interpolate with picewise
            linear function
        """
        return np.interp(self.S0, self.boundary_conds,
                         self.grid[:,0])
    
    """ General pricing method 
        for all relative classes
    """
    def price(self):
        """ NOTE: Calling functions should 
            overwrite the above methods
        """
        self._setup_boundary_conditions_()
        self._setup_coefficients_()
        self._traverse_grid_()
        
        return self._interpolate_()
