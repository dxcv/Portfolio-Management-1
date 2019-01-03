# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 16:29:05 2018

@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
""" Get implied volatilities from a Leisen-Reimer binomial
    tree using the bisection method as the numerical procedure
    
"""
from bisection import bisection
from BinomialCRROption import BinomialCRROption
from BinomialTreeOption import BinomialTreeOption

class ImpliedVolatilityModel( object ):
    def __init__( self, S0, r, T, div, N,
                  is_call = False ):
        self.S0 = S0
        self.r = r
        self.T = T
        self.div = div
        self.N = N
        self.is_call = is_call
    
    def _option_valuation_( self, K, sigma, model ):
        """ Do valuation based on given model:
                Binomial, CRR...
        """
        if model.upper() == "CRR":
            option = BinomialCRROption(
                            self.S0, K, self.r, self.T, self.N,
                            { "sigma":sigma, 
                              "is_call":self.is_call,
                              "div": self.div } )
        else:
            option = BinomialTreeOption(
                            self.S0, K, self.r, self.T, self.N,
                            { "sigma":sigma, 
                              "is_call":self.is_call,
                              "div": self.div } )
        return option.price()
    
    def get_implied_volatilities( self, Ks, opt_prices):
        """ Find implied volatilities given a list of 
            market price inputs Ks as strike and price
            return vol-curve in imp_vol
        """
        imp_vol = []
        for i in range(len(Ks)):
            # Find f(sigma) by bisection method
            # f is defined as in-line function
            f = lambda sigma: self._option_valuation_(Ks[i],sigma)-opt_prices[i]
            vol = bisection( f, 0.01, 0.99, 0.0001, 100)[0]
            imp_vol.append(vol)
        
        return imp_vol
    
import matplotlib.pyplot as plt    
strikes = [ 75, 80, 85, 90, 92.5, 95, 97.5,
            100, 105, 110, 115, 120, 125]
put_prices = [ 0.16, 0.32, 0.6, 1.22, 1.77, 2.54, 3.55,
               4.8, 7.75, 11.8, 15.96, 20.75, 25.81]
model = ImpliedVolatilityModel( 99.62, 0.0248, 78/365., 
                                0.0182, 77, is_call=False )
impvols_put = model.get_implied_volatilities( strikes, put_prices )
plt.plot(strikes, impvols_put)
plt.xlabel('Strike Prices')
plt.ylabel('Implied Volatilities')
plt.title('AAPL Put Implied Volatilities expiring in 78 days')
plt.show()