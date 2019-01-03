# -*- coding: utf-8 -*-
"""
Created on Mon Dec  3 09:46:25 2018
This is the function to back calculate 
forward fx rate basis adjustments
@author: Shaolun Du
@contacts: Shaolun.du@gmail.com
"""
from curve import Curve_Keeper as C_K
from fx import FX_Tools as Tools
from fx import Day_Counter_func as Day_Count
import numpy as np
import pandas as pd
def Cal_implied_rate( fx0, 
                      forward_adj,
                      DF_d,
                      currency ):
    """ Given domestic(USD) discount factors and
        foreign discount factors and 
        market forward term structure
        back calculate the corresponding 
        fx basis adjustments of this currency
        NOTE: currency BRL discount factor convention
              is different from other currency
    """
    # fx_forward is a set of term strutrue with dates and values
    fx_forward = [[ele[0],ele[1]+fx0] for ele in forward_adj]
    df_usd = get_aline_df( fx_forward, 
                           DF_d )
    implied_r = get_implied_rates( fx_forward,
                                   df_usd,
                                   fx0,
                                   currency )
    return implied_r

def get_aline_df( fx_forward, 
                  DFs ):
    """ Get corresponding discount factors aline with 
        dates in fx_forward list which is generated 
        from the market
    """
    ans = []
    idx = 0 
    for loc in range(len(DFs)-1):
        cur_p = DFs[loc]
        nxt_p = DFs[loc+1]
        while idx < (len(fx_forward)-1) and \
            (fx_forward[idx][0]>=cur_p[0] and fx_forward[idx][0]<nxt_p[0]):
                df = Tools.interpolation_act( fx_forward[idx][0],
                                              cur_p[0],
                                              cur_p[1],
                                              nxt_p[0],
                                              nxt_p[1] )
                ans.append([fx_forward[idx][0],df])
                idx += 1
    return ans

def get_implied_rates( fx_forward,
                       df_usd,
                       fx0,
                       currency ):
    """ Back out interests rates given 
        a set of discount factors 
        NOTE: The discount factor curve has different
              conventions which generates quite different
              results BE CAREFUL!
    """
    ans = []
    df_implied = [[e1[0],fx0/e1[1]*e2[1]] for e1,e2 in zip(fx_forward,df_usd)]
    
    sdate = df_usd[0][0]
    if currency.upper() == "BRL":
        for ele in df_implied:
            yearfrac = np.busday_count(sdate, ele[0])/252
            if yearfrac > 0:
                rate = (1/ele[1])**(1/yearfrac)-1
            else:
                rate = 0
            ans.append([ele[0],rate])
    return ans 

####################################
###--- Testing Function Below ---###
sdate = "2018-11-30"
schema_name = "Yield_Curve"
curve_keeper = C_K.Curve_Keeper( sdate, 
                                 schema_name )
currency = "USD"
shock_year = -1
BPS = 0
spread = 0
Day_Counter = Day_Count.Day_Counter("Act/360")
cv = curve_keeper.gen_curve( currency, 
                             shock_year, 
                             BPS,
                             spread,
                             Day_Counter )["FX"]
fx0 = 3.841
f_ccy = "BRL"
forward_adj = [["2018-12-03",15],
               ["2019-01-03",38.33],
               ["2019-02-03",122.07],
               ["2019-03-03",201.5],
               ["2019-04-03",293.33],
               ["2019-05-03",385.17],
               ["2019-06-03",477],
               ["2019-09-03",786],
               ["2019-12-03",1102.38],
               ["2020-12-03",2838],
               ["2021-12-03",5132],
               ["2022-12-03",7672],
               ["2023-12-03",10430],
               ["2024-12-03",13570],
               ["2025-12-03",16710],
               ["2026-12-03",20087],
               ["2027-12-03",23464],
               ["2028-12-03",26842],
              ]
forward_adj = [[pd.to_datetime(ele[0]).date(),ele[1]/10000] for ele in forward_adj]
ans = Cal_implied_rate( fx0, 
                        forward_adj,
                        cv,
                        f_ccy )
print(pd.DataFrame(ans))



