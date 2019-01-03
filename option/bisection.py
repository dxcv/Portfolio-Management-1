# -*- coding: utf-8 -*-
"""
Created on Mon Dec 31 14:21:22 2018

@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""

""" The bisection method """
def bisection(f, a, b, tol=0.01, maxiter=100):
    """
        :param f: The function to solve
        :param a: The x-axis value where f(a)<0
        :param b: The x-axis value where f(b)>0
        :param tol: The precision of the solution
        :param maxiter: Maximum number of iterations
        :return: The x-axis value of the root,
        number of iterations used
        """
    c = (a+b)*0.5 # Declare c as the midpoint ab
    n = 1 # Start with 1 iteration
    while n <= maxiter:
        c = (a+b)*0.5
        if f(c) == 0 or abs(a-b)*0.5 < tol:
            # Root is found or is very close
            return c, n
        n += 1
        if f(c) < 0:
            a = c
        else:
            b = c
    return c, n