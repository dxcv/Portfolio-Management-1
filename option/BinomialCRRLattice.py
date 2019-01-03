# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 11:11:27 2018

@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
""" Price an option by the binomial CRR lattice """
from BinomialCRROption import BinomialCRROption 
import numpy as np

class BinomialCRRLattice(BinomialCRROption):
    ### Overwritting Method
    def _setup_parameters_(self):
        super(BinomialCRRLattice, self)._setup_parameters_()
        self.M = 2*self.N+1
    ### Overwritting Method
    def _initialize_stock_price_tree_(self):
        self.STs = np.zeros(self.M)
        self.STs[0] = self.S0*self.u**self.N
        
        for i in range(self.M)[1:]:
           self.STs[i] = self.STs[i-1]*self.d 
    ### Overwritting Method
    def _initialize_payoff_tree_(self):
        odd_nodes = self.STs[::2]
        return np.maximum( 0, (odd_nodes - self.K) 
                              if self.is_call else (self.K-odd_nodes))
    ### Overwritting Method
    def __check_early_exercise__(self, payoffs, node):
        self.STs = self.STs[1:-1] # Shorten the ends of the list
        odd_STs = self.STs[::2]
        early_ex_payoffs = \
            (odd_STs - self.K) if self.is_call \
            else (self.K - odd_STs)
        payoffs = np.maximum(payoffs, early_ex_payoffs)
            
        return payoffs


#eu_option = BinomialCRRLattice( 6618927,85100000,0.0386,3,10,{ "is_call": False, 
#                                                               "is_eu":   True,
#                                                               "sigma":   0.1 })
#am_option = BinomialCRRLattice( 50,50,0.05,0.5,2,{ "is_call":False,"is_eu":False,
#                                                   "sigma":0.3})
#print(eu_option.price())
#print(am_option.price())

