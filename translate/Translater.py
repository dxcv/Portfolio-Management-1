# -*- coding: utf-8 -*-
"""
Created on Wed Nov 28 13:40:17 2018
This is the object to translate cash flow into 
reporting currency
@author: ACM05
"""
import copy
import DB.dbExecute as dbEx
from collections import OrderedDict
import translate.Translate_Tools  as Tools
import datetime as dt
import translate.Day_Counter_func as Day_Count

class translater():
    def __init__( self,
                  cur_date,
                  curve_keeper ):
        self.cur_date = cur_date
        self.curve_keeper = curve_keeper
        self.spot_rate = self.get_fx_spot_raw( "Yield_Curve" )
    
    def translate_answer( self,
                          answer,
                          target_ccy ):
        """ This is the function to translate
            the structured answer into 
            any given target currency
            the structure should be 
            { {"CF_fv":[...]},
              {"CF_delta":[...]},
              {"Risk":[...]},
              {"Value":[...]},
              }
            NOTE: Risk and Value will be 
                  translated with fx_spot
                  CF_fv and CF_delta will be
                  translated with fx forward rates
        """
        if not answer:
            return {} 
        
        answer_t = copy.deepcopy(answer)
        for name,data in answer_t.items():
            if data["Type"].upper() not in ("FX","XCS"):
                if data["Type"].upper() not in ("SWAP"):
                    d_ccy = data["Currency"]
                elif data["Type"].upper() == "SWAP":
                    d_ccy = data["Currency"]["Leg1"]
                
                if d_ccy != target_ccy:
                    CF_fv = data["CF_fv"]["Net"]
                    CF_delta = data["CF_delta"]["Net"]
                    Risk = data["Risk"]
                    Value = data["Value"]
                    data["CF_fv"]["Net"] = self.translate_cf( CF_fv,
                                                              d_ccy,
                                                              target_ccy )
                    data["CF_delta"]["Net"] = self.translate_cf( CF_delta,
                                                                 d_ccy,
                                                                 target_ccy )
                    for key,val in Value.items():
                        Value[key] = self.translate_spot( Value[key],
                                                          d_ccy,
                                                          target_ccy )
                    for key,val in Risk.items():
                        for cat,value in val.items():
                            val[cat] = self.translate_spot( val[cat],
                                                            d_ccy,
                                                            target_ccy )
                    data["Risk"] = Risk
                    data["Value"] = Value
                    data["Currency"] = d_ccy + "(" + target_ccy + ")"
                    data["FX_fv"] = {"Net":[[ele[0],ele[1]*0.01] for ele in data["CF_fv"]["Net"]]}
                else:
                    data["FX_fv"] = {"Net":[[ele[0],0] for ele in data["CF_fv"]["Net"]]}
            elif data["Type"].upper() in ("FX","XCS"):
                """ FX risk for XCS and FX positions
                    are little complicated
                    since they will have risks on 
                    only one leg 
                    Here we assume:
                            Swap leg one means receive
                                 leg two means pay
                """
                d_ccy = data["Currency"]["Leg1"]
                ccy_1 = data["Currency"]["Leg1"]
                ccy_2 = data["Currency"]["Leg2"]
                
                if ccy_1 != target_ccy:
                    cf_fv_1 = [[ele["End_Time"],ele["PMT"]] for ele in data["Schedule"]["Leg1"]]
                    cf_fv_1 = self.translate_cf( cf_fv_1,
                                                 ccy_1,
                                                 target_ccy )
                else:
                    cf_fv_1 = [[ele["End_Time"],0] for ele in data["Schedule"]["Leg1"]]
                
                if ccy_2 != target_ccy:
                    cf_fv_2 = [[ele["End_Time"],ele["PMT"]] for ele in data["Schedule"]["Leg2"]]
                    cf_fv_2 = self.translate_cf( cf_fv_2,
                                                 ccy_2,
                                                 target_ccy )
                else:
                    cf_fv_2 = [[ele["End_Time"],0] for ele in data["Schedule"]["Leg2"]]
                
                cf_net = [[e1[0],e2[1]-e1[1]] for e1,e2 in zip(cf_fv_1,cf_fv_2)]
                
                data["FX_fv"] = {"Net":[[ele[0],ele[1]*0.01] for ele in cf_net]}
                if d_ccy != target_ccy:
                    CF_fv = data["CF_fv"]["Net"]
                    CF_delta = data["CF_delta"]["Net"]
                    Risk = data["Risk"]
                    Value = data["Value"]
                    data["CF_fv"]["Net"] = self.translate_cf( CF_fv,
                                                               d_ccy,
                                                               target_ccy )
                    data["CF_delta"]["Net"] = self.translate_cf( CF_delta,
                                                                  d_ccy,
                                                                  target_ccy )
                    for key,val in Value.items():
                        Value[key] = self.translate_spot( Value[key],
                                                            d_ccy,
                                                            target_ccy )
                    for key,val in Risk.items():
                        for cat,value in val.items():
                            val[cat] = self.translate_spot( val[cat],
                                                             d_ccy,
                                                             target_ccy )
                    data["Risk"] = Risk
                    data["Value"] = Value
                    data["Currency"] = d_ccy + "(" + target_ccy + ")"
            answer_t[name] = data
        
        return answer_t
        
    def translate_spot( self,
                        raw_val,
                        raw_ccy,
                        target_ccy ):
        """ Translate a single point by 
            current fx rate (fx_spot)
        """
        if target_ccy in ("LCL",""):
            fx0 = 1
        else:
            fx0 = self.spot_rate[target_ccy]/self.spot_rate[raw_ccy]
        return raw_val/fx0
    
    def translate_cf( self,
                      raw_cf,
                      raw_ccy,
                      target_ccy ):
        """ Translate current cash flow table
            into target currency
        """
        if target_ccy in ("LCL",""):
            target_ccy = raw_ccy
        fx0 = self.spot_rate[target_ccy]/self.spot_rate[raw_ccy]
        spread = 0
        ans_cf = []
        Day_Counter = Day_Count.Day_Counter("ACT/365")
        f_cv = self.gen_fx_curve( target_ccy, 
                                  -1, 
                                  0,
                                  spread,
                                  Day_Counter )
        f_cv = Tools.augument_by_frequency(f_cv, 1)
        d_cv = self.gen_fx_curve( raw_ccy, 
                                  -1, 
                                  0,
                                  spread,
                                  Day_Counter )
        d_cv = Tools.augument_by_frequency(d_cv, 1)
        for ele in raw_cf:
            date = ele[0]
            cf = ele[1]
            fx_rate = fx0*self.get_fx_rate( date, f_cv, d_cv)
            ans_cf.append([date,cf*fx_rate])
        return ans_cf
    
    def get_fx_rate( self,
                     date, 
                     f_cv, 
                     d_cv ):
        """ Get fx rate given date
        """
        f_df, d_df = 0,0
        for loc in range(1,len(f_cv)):
            ele = f_cv[loc]
            pre = f_cv[loc-1]
            if ele[0] >= date and date >= f_cv[0][0]:
                f_df = (date-pre[0])/(ele[0]-pre[0])*(ele[1]-pre[1])+pre[1]
                break
        for loc in range(1,len(d_cv)):
            ele = d_cv[loc]
            pre = d_cv[loc-1]
            if ele[0] >= date and date >= d_cv[0][0]:
                d_df = (date-pre[0])/(ele[0]-pre[0])*(ele[1]-pre[1])+pre[1]
                break
        if f_df*d_df == 0:
            print("With in Translater Line:190")
            print("Cannot find date on curve...")
            print(date)
            return 0
        
        return d_df/f_df
    
    def gen_fx_curve( self,
                      currency, 
                      shock_year, 
                      BPS,
                      spread,
                      Day_Counter ):
        
        cv_bk = self.curve_keeper.gen_curve(  currency, 
                                              shock_year, 
                                              BPS,
                                              spread,
                                              Day_Counter )

        cv = cv_bk["FX"]    
        return cv
    
    def get_fx_spot_raw( self, 
                         schema_name ):
        """ This module should not be here but 
            currently do not have a stand alone FX
            module for this project
        """
        ans = {}
        tb_name   = "fx_spot"
        sqlstring = "Select currency, rate from " + tb_name + " where sdate = \'" + self.cur_date +"\'"
        raw_data  = dbEx.dbExecute( schema_name, 
                                    sqlstring )
        for ele in raw_data:
            ans[ele["currency"]] = ele["rate"]
        return ans    
    

