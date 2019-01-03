# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 14:48:22 2018
Price a European option by the binomial tree model
@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""

from StockOption import StockOption
import math
import numpy as np

class BinomialTreeOption(StockOption):
    """ Child object of StockOption
    """
    """ S0, K, r, T, N, params are 
        mother class inputs
    """
    def _setup_parameters_(self):
        self.u = 1+self.pu
        self.d = 1-self.pd
        self.qu = (math.exp((self.r-self.div)*self.dt)-self.d)/(self.u-self.d)
        self.qd = 1-self.qu
    
    def _initialize_stock_price_tree_(self):
        # Initialize terminal price nodes to zeros
        # This is a 2-D tree at T0
        self.STs = [np.array([self.S0])]
        
        # Simulate possible stock path
        for i in range(self.N):
            pre_branches = self.STs[-1]
            st = np.concatenate((pre_branches*self.u,[pre_branches[-1]*self.d]))
            self.STs.append(st) # Add node at each timestap
            
    def _initialize_payoff_tree_(self):
        # Get payoff when option experied at end node
        payoffs = np.maximum(0,(self.STs[self.N]-self.K) if self.is_call else(self.K-self.STs[self.N]))
        
        return payoffs
    def __check_early_exercise__( self, payoffs, node):
        eraly_ex_payoff = \
            (self.STs[node] - self.K) if self.is_call \
            else (self.K-self.STs[node])
        return np.maximum(payoffs,eraly_ex_payoff)
    
    def _traverse_tree_(self, payoffs):
        for i in reversed(range(self.N)):
            # The payoffs from NOT exercing the option
            payoffs = (payoffs[:-1]*self.qu + payoffs[1:]*self.qd)*self.df
            
            # Payoffs from exercising, for American options
            if not self.is_european:
                payoffs = self.__check_early_exercise__( payoffs, i )
        return payoffs
    
    def __begin_tree_traversal__(self):
        payoffs = self._initialize_payoff_tree_()
        
        return self._traverse_tree_(payoffs)
    
    def price(self):
        """ The pricing implementation """
        self._setup_parameters_()
        self._initialize_stock_price_tree_()
        payoffs = self.__begin_tree_traversal__()
        
        return payoffs[0]
    
#eu_option = BinomialTreeOption( 50,50,0.05,0.5,2,{"pu":0.2,"pd":0.2,"is_call":False,"is_eu":True})
#am_option = BinomialTreeOption( 50,50,0.05,0.5,2,{"pu":0.2,"pd":0.2,"is_call":False,"is_eu":False})
#print(eu_option.price())
#print(am_option.price())    