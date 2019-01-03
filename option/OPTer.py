# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 16:01:49 2018
This is the module of option pricing
OPTer takes option type and style type 
to initialize and incorprate both 
black scholes formula and MC simulation method 
to calculation option pricing 
also has the method risk_cal to generate
all greek letters
@author: Shaolun Du
@Contact: Shaolun.du@gmail.com
"""

from option import option_tools as OPT_Tools

class OPTer():
    def __init__( self,
                  MC_Gen,
                  instrument ):
        """ Initial settings for OPTer
            opt_instrument will contain all
            information needed to do pricing
            as well as risk analysis
            opt_instrument = {  "name":....,
                                "type":....,
                                "style":... }
            style = {"Euro","Amer","Berm"...}
            type  = {"stock","forward","fx","irs"}
            opt_direction = {"Put","Call"}
        """
        self.MC_Gen     = MC_Gen
        self.instrument = instrument
    def cal_value( self,
                   vol = "" ):
        """ Calculate option value given a 
            predefined volatility 
        """
        if self.style.upper() == "EUR":
            value,greek = OPT_Tools.BS_E_vanilla_div(self.instrument)
        elif self.style.upper() == "AMER":
            """ For American style option we do not
                have closed form solution in black 
                scholes and the same thing happen to 
                other type of option except european 
                option as well
                Here, MC_*** means we are relying on 
                monte carlo simulation to calculate 
                these options' prices
            """
            value,greek = OPT_Tools.BS_E_vanilla_div(self.instrument)
            



####################################
###--- Quick Testing Function ---###
s_date = "2018-12-14"
m_date = "2020-12-14"

instrument = { "Spot":     100,
               "Strike":   100,
               "Start":    s_date,
               "Maturity": m_date,
               "Interests":0.05,
               "Div":      0,
               "Vol":      0.2,
               "Type":     "call",
                }