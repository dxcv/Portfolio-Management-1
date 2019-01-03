# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 17:09:51 2018
This is the tools function for option
pricing module 
It also relies on the Monte Carlo generation 
object to get sample path 
@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
import numpy as np
import scipy.stats as si

def BS_E_vanilla_div( instrument ):
    #S: spot price
    #K: strike price
    #T: time to maturity
    #r: interest rate
    #q: rate of continuous dividend paying asset 
    #sigma: volatility of underlying asset
    S = instrument["Spot"]
    K = instrument["Strike"]
    B = instrument["Start"]
    M = instrument["Maturity"]
    r = instrument["Interests"]
    q = instrument["Div"]
    sigma = instrument["Vol"]
    option = instrument["Type"]
    T = (M-B).days/365
    
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = (np.log(S / K) + (r - q - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    if option.upper() == "CALL":
        result = (S * np.exp(-q * T) * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0))
    if option.upper() == "PUT":
        result = (K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * np.exp(-q * T) * si.norm.cdf(-d1, 0.0, 1.0))
    
    return result
