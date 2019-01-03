# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 14:18:29 2018
Store common arrtibutes of stock option
@author: Shaolun Du
@Contact: Shaolun.du@gmail.com
"""
import math

class StockOption(object):
    
    def __init__(self, S0, K, r, T, N, params):
        self.S0 = S0
        self.K = K
        self.r = r
        self.T = T
        self.N = max(1,N)
        self.STs = None # Declare stock price tree
        
        """ Optional parameters used by derived classes
        """
        self.pu = params.get("pu",0) # probability up
        self.pd = params.get("pd",0) # probability down
        self.div = params.get("div",0) # Dividend yield
        self.sigma = params.get("sigma",0) # Volatility
        self.is_call = params.get("is_call",True)
        self.is_european = params.get("is_eu",True)
        
        self.dt = T/float(N) # Single time step, in years
        self.df = math.exp(-(r-self.div)*self.dt) # DF



