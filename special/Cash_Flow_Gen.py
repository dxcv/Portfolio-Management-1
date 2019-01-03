# -*- coding: utf-8 -*-
"""
Created on Sun Nov  4 12:34:17 2018
Cash Flow generation based on customized balance table

@author: shaol
"""

import pandas as pd
import bond.bond_tools  as Tools
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from datetime import date

def CF_Gen( cf_insturments, 
            curve,
            cv_keeper,
            Day_Counter,
            itype ):
    """ Here cash flow generator is a little complicated
        we have to consider accruing based cash flow generation
        which means we calculate cash flow but only paid
        at the payment date
        NOTE: Here the underlying condition is payment frequency
        should be a multiple of accruing frequency and assume the smallest
        unit is 1 month
        Also the balance table should be the begin balance on that period
        We add a new functionality here to handle 
        just a fixed of cash flow happens
        on the corresponding date shown in the balance table
    """
    if itype.upper() in ("CASH","CF"):
        return Cash_Gen( cf_insturments, 
                         curve,
                         cv_keeper,
                         Day_Counter )
    elif itype.upper() == "REGULAR":
        return Bond_Gen( cf_insturments, 
                         curve,
                         cv_keeper,
                         Day_Counter )

def Cash_Gen( cf_insturments, 
              curve,
              cv_keeper,
              Day_Counter ):
    """ This is a cash item generater which
        output cash flow on the inputs table and 
        fix the cash flow right on the corresponding dates
    """
    balance_tb   = cf_insturments["balance_tb"]
    """ Looping through balance table and make a fixing
        on each accrued_freq date and we assume that balance table 
        is coincidence with fixing rate table
    """
    cf_tb =[]
    ans_li  = []
    cf_tb = balance_tb.copy()
    cf_tb.append(balance_tb[-1])
    for idx, ele in enumerate(cf_tb[:-1]):
        ans_li.append( OrderedDict({ 
                                "Beg_Time":   ele[0],
                                "End_Time":    ele[0], 
                                "Beg_balance": 0,
                                "PMT":      ele[1],
                                "Principal":0,
                                "Interests":0,
                                "Rates":    0, } ))
    return ans_li

def Bond_Gen( cf_insturments, 
              curve,
              cv_keeper,
              Day_Counter ):
    """ Here cash flow generator is a little complicated
        we have to consider accruing based cash flow generation
        which means we calculate cash flow but only paid
        at the payment date
        NOTE: Here the underlying condition is payment frequency
        should be a multiple of accruing frequency and assume the smallest
        unit is 1 month
        Also the balance table should be the begin balance on that period
    """
    """ cf_instruements = {  "currency":...,
                             "balance_tb":...,
                             "acc_cpn_detail":...,
                             "pay_convention":....,
                             "day_convention":....,}
        cf_insturments["acc_cpn_detail"] = [[ period,    "Rate_type",
                                             "xxx/xML", spread  ],[...],[...]...]
    """  
    currency     = cf_insturments["currency"]
    balance_tb   = cf_insturments["balance_tb"]
    coupons      = cf_insturments["acc_cpn_detail"]
    pay_freq     = cf_insturments["pay_convention"]
    """ Looping through balance table and make a fixing
        on each accrued_freq date and we assume that balance table 
        is coincidence with fixing rate table
    """
    bal_tb =[]
    ans_li  = []
    loc_ind = 0
    bal_tb = balance_tb.copy()
    bal_tb.append(balance_tb[-1])
    r_type = coupons[loc_ind][1]
    spreads= coupons[loc_ind][3]
    Rate_floor = float(coupons[loc_ind][4])
    Rate_cap = float(coupons[loc_ind][5])
    for idx, ele in enumerate(bal_tb[:-1]):
        """ idx is the index number here it
            works as the period number
        """
        next_t = bal_tb[idx+1][0]
        year_frac = Day_Counter.yearfrac( ele[0], next_t )
        if idx > coupons[loc_ind][0]:
            loc_ind += 1
            r_type = coupons[loc_ind][1]
            spreads= coupons[loc_ind][3]
        
        if r_type == "CMS":
            cur_fwd_p = get_fwd_month(coupons[loc_ind][2])
            fwd_rate = Tools.get_CMS_rate( curve, 
                                           ele[0], 
                                           cur_fwd_p,
                                           Day_Counter,
                                           cv_keeper,
                                           currency )
        elif r_type.upper() == "LIBOR":
            cur_fwd_p = get_fwd_month(coupons[loc_ind][2])
            fwd_rate = Tools.get_fwd_rate( curve, 
                                           ele[0], 
                                           cur_fwd_p,
                                           Day_Counter,
                                           cv_keeper,
                                           currency )
            if year_frac == 0:
                fwd_rate = 0
            else:
                fwd_rate = fwd_rate/year_frac
        elif r_type.upper() == "FIX":
            fwd_rate = coupons[loc_ind][2]
        elif r_type.upper() == "TJLP":
            start_time = ele[0]
            """ TLP is special we have to look into 
                data base if we have a TJLP rates
                then use it otherwise we use regression
            """
            months = start_time.month
            if months > 0 and months <= 3:
                start_time = date(start_time.year, 1, 1)
            if months > 3 and months <= 6:
                start_time = date(start_time.year, 4, 1)
            if months > 6 and months <= 9:
                start_time = date(start_time.year, 7, 1)
            if months > 9 and months <= 12:
                start_time = date(start_time.year, 10, 1)
                
            if start_time < curve[0][0]:
                Rates_Curve = cv_keeper.get_other_by_type( "TJLP" )
                for loc in range(len(Rates_Curve)-1):
                    cur_pt = Rates_Curve[loc]
                    nxt_pt = Rates_Curve[loc+1]
                    if start_time >= cur_pt[0] and \
                        start_time < nxt_pt[0]:
                            
                        fwd_rate = cur_pt[1]
                        break
            else:
                fwd_rate = Tools.get_CMS_rate( Rates_Curve, 
                                               start_time, 
                                               60,
                                               Day_Counter,
                                               cv_keeper,
                                               currency )
                """ This function comes from TLP regression
                """
                fwd_rate = fwd_rate*0.547 +0.038
        elif r_type.upper() == "CDI":
            cur_fwd_p = 12
            start_time = ele[0]
            """ Even special for CDI modeling
                we have to model accrual based on real
                CDI rate but using approximation
                for forward CDI
            """
            pre_time = date(start_time.year, 1, 1)
                
            if pre_time < curve[0][0]:
                cv_1 = cv_keeper.get_other_by_type( "Brazil CDI" )
                if start_time >= curve[0][0]:
                    w_rates = [ele[1] for ele in cv_1 if ele[0] >= pre_time and ele[0] <= curve[0][0]]
                    rate_1 = sum(w_rates)/len(w_rates)
                    rate_2 = Tools.get_fwd_rate( curve, 
                                                   curve[0][0], 
                                                   cur_fwd_p,
                                                   Day_Counter,
                                                   cv_keeper,
                                                   currency )
                    t_frac = (curve[0][0]-pre_time).days/90
                    fwd_rate = rate_1*t_frac + rate_2*(1-t_frac)
                elif start_time < curve[0][0]:
                    w_rates = [ele[1] for ele in cv_1 if ele[0] >= pre_time and ele[0] <= start_time]
                    fwd_rate = sum(w_rates)/len(w_rates)
            else:
                fwd_rate = Tools.get_fwd_rate( curve, 
                                               pre_time, 
                                               cur_fwd_p,
                                               Day_Counter,
                                               cv_keeper,
                                               currency )
        elif r_type.upper() == "IPCA":
            start_time = ele[0]
            """ TLP is special we have to look into 
                data base if we have a TJLP rates
                then use it otherwise we use regression
            """
            start_time = date(start_time.year, start_time.month, 28)
                
            if start_time < curve[0][0]:
                curve1 = cv_keeper.get_other_by_type( "IPCA" )
                for loc in range(len(curve1)-1):
                    cur_pt = curve1[loc]
                    nxt_pt = curve1[loc+1]
                    if start_time >= cur_pt[0] and \
                        start_time < nxt_pt[0]:
                        fwd_rate = cur_pt[1]
                        break
            else:
                fwd_rate = Tools.get_CMS_rate( curve, 
                                               start_time, 
                                               12,
                                               Day_Counter,
                                               cv_keeper,
                                               currency )
                
                fwd_rate = fwd_rate*0.968 - 0.041
                
            
        """ Apply option effects onto fwd_rates
        """
        
        fwd_rate = max(Rate_floor,fwd_rate)
        fwd_rate = min(Rate_cap,fwd_rate)
        fwd_rate += spreads
        
        ints = ele[1]*fwd_rate*year_frac
        Principal = -(bal_tb[idx+1][1]-ele[1])
        
        ans_li.append( OrderedDict(
                                { "Beg_Time":   ele[0],
                                  "End_Time":    next_t, 
                                  "Beg_balance": ele[1],
                                  "PMT":      ints + Principal,
                                  "Principal":Principal,
                                  "Interests":ints,
                                  "Rates":    fwd_rate, }
                        ) )
    
    """ After accruing coupons we have to regroup them
        into actual paying coupons at the end of each payment period
    """
    ans_li = ans_li[:-1]
    #ans_li = CF_resample( ans_li, pay_freq )
    
    return ans_li
        
def CF_resample( cash_flow, 
                 pay_freq ):
    """ regrouping a given cash flow 
        to make a actual payment from accruing based
        payment sechdule
    """
    ans_li = []
    loc_ind = 0
    cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1])  
    next_pay_date = cash_flow[0]["Beg_Time"] + relativedelta( months = cur_fwd_p )
    next_pay_date = Tools.last_day_of_month(next_pay_date)
    cf1 = cash_flow[0]
    temp = OrderedDict( { "Beg_Time":    cf1["Beg_Time"],
                          "End_Time":    cf1["End_Time"], 
                          "Beg_balance": cf1["Beg_balance"],
                          "PMT":         cf1["PMT"],
                          "Principal":   cf1["Principal"],
                          "Interests":   cf1["Interests"],
                          "Rates":       cf1["Rates"], } )
    for idx, ele in enumerate(cash_flow[:-1]):
        if idx > pay_freq[loc_ind][0]:
            """ Condition if we move one pay
                specification forward
            """
            loc_ind += 1
        if ele["End_Time"] > next_pay_date or idx >= len(cash_flow)-1:
            ans_li.append(temp)
            cur_fwd_p = get_fwd_month(pay_freq[loc_ind][1])  
            next_pay_date = ele["Beg_Time"] + relativedelta(months = cur_fwd_p)
            next_pay_date = Tools.last_day_of_month(next_pay_date)
            temp = OrderedDict({ "Beg_Time":    ele["Beg_Time"],
                                 "End_Time":    ele["End_Time"], 
                                 "Beg_balance": ele["Beg_balance"],
                                 "PMT":         ele["PMT"],
                                 "Principal":   ele["Principal"],
                                 "Interests":   ele["Interests"],
                                 "Rates":       ele["Rates"], })
        if ele["End_Time"] <= next_pay_date:
            temp["End_Time"] = ele["End_Time"]
            temp["PMT"] += ele["PMT"]
            temp["Principal"] += ele["Principal"]
            temp["Interests"] += ele["Interests"]
            
    return ans_li
    
        
def get_fwd_month( fwd_freq ):
    """ given inputs fwd_freq in the format of "XXM"
    """
    if fwd_freq[-1].upper() == "M":
        ans = int(fwd_freq[:-1])
    return ans 



    
