# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 15:40:29 2018

@author: ACM05
"""
""" Implementation of Cox_Ross_Rubinstein model """

from BinomialTreeOption import BinomialTreeOption 
import math

class BinomialCRROption(BinomialTreeOption):
    """ Overwrite of initialization method """
    ### Overwritting
    def _setup_parameters_(self):
        self.u = math.exp(self.sigma*math.sqrt(self.dt))
        self.d = 1.0/self.u
        self.qu = (math.exp((self.r-self.div)*self.dt) -\
                    self.d)/(self.u-self.d)
        self.qd = 1-self.qu
