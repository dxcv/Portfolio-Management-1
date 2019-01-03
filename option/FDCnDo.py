# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 14:16:41 2018

@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
""" Crank_Nicolson method of Finite Differences 
    Pricing Down-and-Out option
"""
import numpy as np
from FDCnEu import FDCnEu

class FDCnDo(FDCnEu):
    """ An instance of Finite difference
        prototype also an overwritting of
        FDCnEu calss
    """
    ### Overwrite the initilize method
    def __init__( self, S0, K,r ,T, sigma,
                  Sbarrier, Smax, M, N, is_call = True):
        super(FDCnEu, self).__init__( S0, K, r, T, 
                                      sigma, Smax, 
                                      M, N, is_call )
        self.dS = (Smax-Sbarrier)/float(self.M)
        self.boundary_conds = np.linspace( Sbarrier,
                                           Smax,
                                           self.M+1 )
        self.i_values = self.boundary_conds/self.dS
        
        
###--- Quick testing ---###
#opt1 = FDCnDo(50,50,0.1,5.0/12.0,0.4,40,100,120,500, True)
#print(opt1.price())
#
#opt2 = FDCnDo(50,50,0.1,5.0/12.0,0.4,40,100,120,500, False)
#print(opt2.price())