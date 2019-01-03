# -*- coding: utf-8 -*-
"""
Created on Tue Dec 18 13:36:42 2018
This is the file to generate random
sequence based on given distribution
and also incorporate of antithetic version
to minimize the time cost
@author: Shaolun Du
@contact:Shaolun.du@gmail.com
"""
import numpy as np
import math
class randomer():
    def __init__( self,
                  distribution ):
        """ Initilize a random generator
            with a given distribution
            path_length means size of path
            sample_size means number of path
        """
        self.distribution = distribution
    
    def get_exp_path( self,
                      instrument,
                      path_length ):
        """ Generate expentional random path
            based on initial price s0 and 
            path_length
        """
        st = instrument["Spot"]
        r  = instrument["Interests"]
        vol= instrument["Vol"]
        s1 = st
        s2 = st
        ans1,ans2 = [st],[st]
        path1,path2 = self.antithetic_seq(path_length)
        for e1,e2 in zip(path1,path2):
            t1 = (r-vol*vol/2)+vol*e1
            t2 = (r-vol*vol/2)+vol*e2
            s1 = s1*math.exp(t1)
            s2 = s2*math.exp(t2)
            ans1.append(s1)
            ans2.append(s2)
        return ans1,ans2
    
    def antithetic_seq( self,
                        path_length ):
        """ Generate antithetic version
            of random path 
        """
        pos_path = self.gen_seq( path_length, 1 )
        neg_path = self.gen_seq( path_length, -1 )
        return pos_path,neg_path
        
    def gen_seq( self,
                 path_length,
                 multi = 1 ):
        """ Generate random path 
        """
        ans = []
        if self.distribution.upper() == "NORM":
            """ Normal distribution
            """
            ans = np.random.normal( 0, 1, path_length )*multi
        else:
            """ Other distribution not done yet...
            """
            ans = []
        
        return ans

###############################
###--- Quick Testing ---###
instrument = { "Spot": 1,
               "Interests": 0.0001,
               "Vol": 0.01 }
generator = randomer("NORM")
p1,p2 = generator.get_exp_path( instrument, 1000 )
print(p1)
print(p2)
    