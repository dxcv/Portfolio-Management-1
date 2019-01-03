# -*- coding: utf-8 -*-
""" This file stands for calculation of FX related problems
    This object has to pre-run all
    currency yield curve in order to
    convert a given currency into 
    any other currency we need
    @author: shaolundu
    @contacts:shaolun.du@gmail.com
"""
import pandas as pd
from collections import OrderedDict
import datetime as dt
import dbExecute as dbEx
from dateutil.relativedelta import relativedelta
import Boot_Strapping as BS_BT
import Boot_Strap_Tools_Func as BS_TF
import Swap_Day_Convention as DC_SWAP
import Day_Counter_func as DT_Func

class FX_Calculator:
    """ This is the calculator for 
        FX related issues for example:
            currency converting
            timeseries cf converting
    """
    def __init__( self,
                  sdate,
                  schema_name,
                  Curve_keeper = "", ):
        self.sdate = sdate
        self.Curve_keeper = Curve_keeper
        self.spot_rate    = self.get_fx_spot_raw( schema_name )
        """ FX curve input data includes the basis
            swap adjustments which is totally
            different from original yield curve
            here name it as fx_curve
        """
        tb_name = "fx_curve"
        self.FX_Rates  = self.get_raw_data( sdate, 
                                            schema_name, 
                                            tb_name )
        self.curve_book= {}
        self.set_all_curves()
        
#################################################
###--- FX converting calculation functions ---###
    def cal_fx_by_cf( self,
                      mode, 
                      data, 
                      d_ccy, 
                      f_ccy ):
        """ Data is a list of dictionaries could be both 
                risk data and cash flow data
            Return value is a list of tupes 
                [...[Yn, translated cash flow based on IRP]...]
            mode = "Risk" means dealing risk metrics
            mode = "CF" means dealing annually cash flow
        """
        if f_ccy == "ALL":
            f_ccy = d_ccy
        d_rate = self.get_spot_ccy( d_ccy )
        f_rate = self.get_spot_ccy( f_ccy )
        spot_rate  = f_rate/d_rate
        fore_curve = self.get_curve_ccy( f_ccy )
        dome_curve = self.get_curve_ccy( d_ccy )
        fore_curve = self.aug_by_frequency( fore_curve[0][0],
                                            fore_curve, 12 )
        dome_curve = self.aug_by_frequency( dome_curve[0][0],
                                            dome_curve, 12 )
       
        rate_list = self.get_fx_rate_li( spot_rate,
                                         fore_curve,
                                         dome_curve )
        
        skip_li = [ "CUSIP","Project Name","Country",
                    "Currency","Industry","Type","CPTY",
                    "Start Date","Maturity Date",
                    "CF_WAL(Y)", "Coupon","Discount"]
        ans = OrderedDict()
        for key in skip_li:
            """ First insert all necessary columns
            """
            if key == "Currency" and f_ccy != d_ccy:
                ans[key] = data[key] + "(" + f_ccy + ")"
            else:
                ans[key] = data[key]
            
        """ Specific individual columns by 
            different type of reporting staff
        """
        if mode.upper() == "RISK":
            key_rate_li = [ "KRD01(K/BPS)",	"KRD02(K/BPS)",	"KRD03(K/BPS)",	
                            "KRD05(K/BPS)",	"KRD07(K/BPS)",	"KRD10(K/BPS)",	
                            "KRD15(K/BPS)",	"KRD20(K/BPS)",	"KRD25(K/BPS)",	
                            "KRD30(K/BPS)",	"KRD40(K/BPS)" ]
            all_rate_li = [ "Notional(K)", "FX01(k/%)", 
                            "NPV(k)", "PV01(k)" ]
            loc = 0
            for key in all_rate_li:
                if key in data:
                    ans[key] = data[key]*spot_rate
            #ans["FX01(k/%)"] = ans[key]*0.01
            for key in key_rate_li:
                ans[key] = data[key_rate_li[loc]]*rate_list[loc+1]
                loc += 1
        elif mode.upper() == "CASH" or mode.upper() == "FV":
            loc = 0
            ans["Notional(K)"] = data["Notional(K)"]*spot_rate
            if mode == "CASH":
                ans["NPV(k)"]  = data["NPV(k)"]*spot_rate
            if mode == "FV":
                ans["DCF_CFSen(k)"] = data["DCF_CFSen(k)"]*spot_rate
                ans["CFSen3(k)"] = data["CFSen3(k)"]*spot_rate
            #ans["FX01(k/%)"]   = ans["NPV(k)"]*0.01
            if "CF_Y00(k)" in data:
                ans["CF_Y00(k)"] = data["CF_Y00(k)"]*spot_rate
            for key,val in data.items():
                if key not in skip_li \
                    and key not in ["CF_Y00(k)","Notional(K)","NPV(k)"]:
                        data[key] = val*rate_list[loc]
                        ans[key]  = data[key]
                        loc += 1
        elif mode.upper() == "FX":
            Day_Counter= DT_Func.Day_Counter('30/360') 
            disc_list  = self.Curve_keeper.gen_fx_dic_li( d_ccy, 
                                                          0, 
                                                          0,
                                                          3,
                                                          Day_Counter )
            d_type = data["Type"]
            if d_type.upper() == "ASSET":
                multi = -1
            elif d_type.upper() == "LIABILITY":
                multi = -1
            else:
                multi = 1
            
            skip_li = [ "CUSIP", "Project Name", "Country", 
                        "Currency", "Industry", "Type", "CPTY",
                        "Start Date", "Maturity Date","CF_WAL(Y)",
                        "Coupon", "Notional(K)", "NPV(k)", 
                        "PV01(k)","Discount" ]
            loc = 0
            ans["Notional(K)"] = data["Notional(K)"]*spot_rate 
            ans["FX01(k/%)"] = 0
            ans["DCF_FXSen(k)"] = 0
            for key,val in data.items():
                if key not in skip_li:
                    if d_ccy != f_ccy and val == val:
                        ans["FX01(k/%)"] = ans["FX01(k/%)"] + multi*val*rate_list[loc]*0.01
                        ans["DCF_FXSen(k)"] = ans["DCF_FXSen(k)"] + multi*val*disc_list[loc]*rate_list[loc]*0.01
                        ans[key] = multi*val*rate_list[loc]*0.01
                    else:
                        ans[key] = 0
                    loc += 1  
        elif mode == "TOP":
            ans["Notional(K)"] = data["Notional(K)"]*spot_rate
            ans["NPV(k)"] = data["NPV(k)"]*spot_rate
            ans["PV01(k)"] = data["PV01(k)"]*spot_rate
            ans["DCF_CFSen(k)"]= data["DCF_CFSen(k)"]*spot_rate
            if d_ccy == f_ccy:
                ans["FX01(k/%)"] = 0
                #ans["DCF_FXSen(k)"] = 0
            else:
                ans["FX01(k/%)"] = data["FX01(k/%)"]*spot_rate
                #ans["DCF_FXSen(k)"] = data["DCF_FXSen(k)"]*spot_rate
            ans["DCF_FXSen(k)"] = 0
        return ans
    
    def get_fx_rate_li( self,
                        spot_rate,
                        fore_curve,
                        dome_curve ):
        """ Current implementaion is not exact
            Only works for output translation
            return value is a list of annually 
            fx rates = [fx1,fx2,fx3,...]
        """
        ans = [spot_rate]
        frequency = relativedelta( months = 12 )
        sdate = fore_curve[0][0] + frequency
        edate = fore_curve[0][0] + 40*frequency
        loc_for, loc_dom = 0, 0
        while sdate < edate:
            if fore_curve[loc_for][0] >= edate:
                break
            if dome_curve[loc_dom][0] >= edate:
                break
            dom_dist = dome_curve[loc_dom-1][1] + \
                            (dome_curve[loc_dom][1]-dome_curve[loc_dom-1][1])\
                            *(sdate-dome_curve[loc_dom-1][0]).days/\
                            (dome_curve[loc_dom][0]-dome_curve[loc_dom-1][0]).days
            for_dist = fore_curve[loc_for-1][1] + \
                        (fore_curve[loc_for][1]-fore_curve[loc_for-1][1])\
                        *(sdate-fore_curve[loc_for-1][0]).days/\
                        (fore_curve[loc_for][0]-fore_curve[loc_for-1][0]).days
            
            ans.append(spot_rate*dom_dist/for_dist)
            sdate += frequency   
            loc_for += 1
            loc_dom += 1
        
        return ans

###--- END FX converting calculation ---###
#################################################

###############################################
###--- Curve generation helper functions ---###
    def aug_by_frequency( self,
                          sdate,
                          data,
                          freq ):
        if type(sdate) is str:
            sdate = dt.datetime.strptime(sdate, '%Y-%m-%d').date()
        ans = []
        freq = relativedelta(months = freq)
        for loc in range(len(data)-1):
            cur_point = data[loc]
            nxt_point = data[loc+1]
            while sdate >= cur_point[0] \
              and sdate < nxt_point[0] \
              and nxt_point[0] > cur_point[0]:
                  df = cur_point[1] + (nxt_point[1]-cur_point[1])*(sdate-cur_point[0]).days/(nxt_point[0]-cur_point[0]).days
                  ans.append([sdate,df])
                  sdate += freq
                  next_month = sdate.replace(day=28) + dt.timedelta(days=4)
                  sdate  = next_month - dt.timedelta(days=next_month.day)
                  #sdate += freq
        return ans

    def get_curve_ccy( self,
                       ccy ):
        ticker = "FX" + "_" + ccy.upper() + \
                    "_" + str(self.sdate)
        return self.curve_book[ticker]
    
    def set_all_curves( self ):
        for ccy,val in self.FX_Rates.items():
            convention  = DC_SWAP.get_convention_by_currency(ccy)["LIBOR_day_count"]
            Day_Counter = DT_Func.Day_Counter(convention)
            curve  = self.gen_curve( ccy, 
                                     Day_Counter )
            self.set_curves( self.sdate,
                             ccy,
                             "FX",
                             curve )
    
    def set_curves( self,
                    sdate,
                    currency,
                    type_name,
                    curve ):
        ticker = type_name + "_" + currency.upper() + \
                    "_" + str(sdate)
        if not ticker in self.curve_book:
            self.curve_book[ticker] = curve   
    
    def gen_curve( self,
                   ccy,
                   Day_Counter ):
        """ Make its own curve for all currency 
            with basis spread adjustments
        """
        ans_book = self.FX_Rates[ccy]
        convention = DC_SWAP.get_convention_by_currency( ccy )
        FX_curve = BS_BT.boot_strapping_LIBOR( self.sdate,
                                               convention, 
                                               ans_book, 
                                               Day_Counter )
        return FX_curve

        
###--- End Curve generation helper ---###   
###############################################

##################################
###--- Spot rates functions ---###     
    
    def get_fx_spot_raw( self, 
                         schema_name ):
        """ This module should not be here but 
            currently do not have a stand alone FX
            module for this project
        """
        tb_name   = "fx_spot"
        sqlstring = "Select currency, rate from " + tb_name + " where sdate = \'" + self.sdate +"\'"
        raw_data  = dbEx.dbExecute( schema_name, 
                                    sqlstring )
        return raw_data
    
    def get_spot_ccy( self,
                      ccy ):
        """ Return rate by currency
        """
        rate = [ele["rate"] for ele in self.spot_rate if ele["currency"] == ccy][0]
        return rate    

###--- End of Spot rates functions ---###     
#########################################

##############################################
###--- A copy of Curve keeper functions ---###    
    def get_raw_data( self,
                      sdate, 
                      schema_name, 
                      table_name ):
        """ Get data from DB and generate
            data annually for SWAP and OIS
            !Important that is why we have
            augument_by_frequency functions
            Return value is a dictionary of 
            all currencies with dictionary 
                {
                 "cash":..., 
                 "future":..., 
                 "swap":...,
                 }
            inside
        """
        sqlstring = "Select * from " + table_name + " where sdate = \'" + sdate + "\'"
        raw_data  = dbEx.dbExecute( schema_name, sqlstring )
        if table_name in ("fx_curve","yield_curve"):
            sqlstring = "Select * from curve_setting"
            raw_setting = dbEx.dbExecute( schema_name, sqlstring )
        
        all_ccy   = set([ele["currency"] for ele in raw_data])
        ans_book  = {}
        
        for ccy in all_ccy:
            Cash_Num   = 7
            Future_Num = 0
            Swap_Num   = [ele["number"] for ele in raw_setting \
                          if ele["currency"].upper() == ccy \
                          and ele["name"].upper() == "SWAP"][0]
            data = [ele for ele in raw_data if ele["currency"].upper() == ccy]
            data_CASH   = self.get_rates_by_type( data, "cash" )
            data_FUTURE = self.get_rates_by_type( data, "future" )
            data_SWAP   = self.get_rates_by_type( data, "swap" )
            data_SWAP   = BS_TF.augument_by_frequency( data_SWAP, 12 )
            ans_book[ccy] = {
                            "cash"  : [data_CASH,Cash_Num],
                            "future": [data_FUTURE,Future_Num],
                            "swap"  : [data_SWAP,Swap_Num],
                            }
        return ans_book
    
    def get_rates_by_type( self,
                           data_book = {},
                           ins_type  = "" ):
        
        """ Data_book should be a list of dictionary record
            ins_type should be a string to search
            return value is still a list of dictionaries
        """
        data = [ele for ele in data_book if ele["type"].upper() == ins_type.upper()]
        sorted_by_date = sorted(data, key=lambda tup: tup["maturity"])
        ans = [[ele['maturity'], ele['rates']] for ele in sorted_by_date]
        
        return ans

###--- End of Curve keeper functions ---###   
###########################################
