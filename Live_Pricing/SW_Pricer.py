# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 11:47:22 2018
This is a swap object which can be used to handle 
all swap related requirements 

@author: ACM05
"""
import pandas as pd
import datetime as dt
from collections import OrderedDict

import DB.dbExecute as dbEx
from curve import Boot_Strapping as B_S
from curve import Boot_Strap_Tools_Func as BS_TF
from Live_Pricing import Swap_Tools  as Tools
from Live_Pricing import Day_Counter_func as Day_Count
from Live_Pricing.Cash_Flow_Gen import CF_Gen as CF_Gen

class Pricer:
    def __init__( self,
                  curve_instrument,
                  cv_fx_instrument,
                  fx_spot,
                  cv_keeper = "" ):
        """ Initial settings for swaper
            swap_instrument will contain all
            information needed to do pricing
            as well as risk analysis
            swap_instrument = { "name":....,
                                "leg1":....,
                                "leg2":... }
            curve_instrument = {"currency":[...curve instrumentss]}
        """
        self.fx_spot     = fx_spot
        self.cv_keeper   = cv_keeper
        self.answer_bk   = OrderedDict()
        self.instruments = OrderedDict()
        self.curve_instrument = curve_instrument
        self.cv_fx_instrument = cv_fx_instrument
        self.convention = {  
                            'USD':{ 'fix':{ 'freq':2,},
                                    'float':{'freq':4,},
                                    'LIBOR_day_count':'30/360',
                                    'OIS_day_count':'ACT/360', },
                            'EUR':{ 'fix':{ 'freq':1, },
                                    'float':{ 'freq':2,},
                                    'LIBOR_day_count':'30/360',
                                    'OIS_day_count':'ACT/360',},
                            'GBP':{ 'fix':{ 'freq':2,},
                                    'float':{ 'freq':2,},
                                    'LIBOR_day_count':'ACT/365',
                                    'OIS_day_count':'ACT/365',},
                            'JPY':{ 'fix':{ 'freq':2,},
                                    'float':{ 'freq':2,},
                                    'LIBOR_day_count':'ACT/365',
                                    'OIS_day_count':'ACT/365', },
                            'CAD':{ 'fix':{ 'freq':2,},
                                    'float':{ 'freq':2,},
                                    'LIBOR_day_count':'ACT/365',
                                    'OIS_day_count':'ACT/365', },
                            'CHF':{ 'fix':{ 'freq':1,},
                                    'float':{ 'freq':2,},
                                    'LIBOR_day_count':'30/360',
                                    'OIS_day_count':'ACT/360', },
                            'BRL':{ 'fix':{ 'freq':2,},
                                    'float':{ 'freq':2,},
                                    'LIBOR_day_count':'30/360',
                                    'OIS_day_count':'ACT/360',},
                            'COP':{ 'fix':{ 'freq':4,},
                                    'float':{ 'freq':4,},
                                    'LIBOR_day_count':'ACT/360',
                                    'OIS_day_count':'ACT/360',},
                        }
                            
    def get_raw_dfs( self,
                     value_date,
                     currency ):
        """ Add on function to generate 
            both libor discount factors
            and fx (basis adjusted)
            disocunt factors
        """
        convention    = self.convention[currency]
        Day_Counter   = Day_Count.Day_Counter(convention["LIBOR_day_count"])
        cv_instrument = self.curve_instrument[currency]
        fx_instrument = self.cv_fx_instrument[currency]
        if currency.upper() != "BRL": 
            cv_dis = self.gen_swap_curve( value_date,
                                          convention,
                                          cv_instrument, 
                                          "",
                                          Day_Counter )
            fx_dis = self.gen_swap_curve( value_date,
                                          convention,
                                          fx_instrument, 
                                          "",
                                          Day_Counter )
        else:
            cv_dis = self.gen_zero_curve( value_date,
                                          convention,
                                          cv_instrument, 
                                          "",
                                          Day_Counter )
            fx_dis = self.gen_zero_curve( value_date,
                                          convention,
                                          fx_instrument, 
                                          "",
                                          Day_Counter )
            
        cv_dis = Tools.augument_by_frequency( cv_dis,
                                                  1,
                                                  "" )
        fx_dis = Tools.augument_by_frequency( fx_dis,
                                              1,
                                              "" )
        return cv_dis,fx_dis
        
        
    def add( self, name, instrument, disc_cv_details ):
        """ Add position into Pricer
        """ 
        instr = self.gen_swap_instruments( instrument )
        self.instruments[name] = [instr,disc_cv_details]
        
    def price_swap( self,
                    sw_name,
                    value_date ):
        """ Pricing a swap based on the 
            valuation date and the corrresponding
            swap name
        """
        [instr,disc_cv_details] = self.instruments[sw_name]
        ccy1_spot = self.fx_spot[instr["leg1"]["currency"]]
        ccy2_spot = self.fx_spot[instr["leg2"]["currency"]]
        fx_spot   = ccy1_spot/ccy2_spot
        L1_INT,L1_PRI = self.get_NPVs( "leg1",
                                       value_date,
                                       instr,
                                       disc_cv_details )
        L2_INT,L2_PRI = self.get_NPVs( "leg2",
                                       value_date,
                                       instr,
                                       disc_cv_details )
        if instr["leg2"]["acc_cpn_detail"][0][2] == 1:
            npv = 0
        else:
            npv = L1_INT+L1_PRI-L2_PRI*fx_spot-L2_INT*fx_spot
        pre_rate   = instr["leg2"]["acc_cpn_detail"][0][2]
        fixed_rate = (L1_INT+L1_PRI-L2_PRI*fx_spot)/(L2_INT/pre_rate*fx_spot)
        
        return fixed_rate,npv
    
    def get_NPVs( self,
                  leg,
                  value_date,
                  instrument,
                  disc_cv_details ):
        """ Disc_cv_details is the specification
            of which discounting curve to use
            when calculating NPV as well as risk analysis
            disc_cv_details = {
                                "type":...,
                                "spread":...,}
        """
        """ Step one cal of leg1 
            leg1 = { "currency":...,
                     "balance_tb":...,
                     "acc_cpn_detail":...,
                     "pay_convention":....,
                     "day_convention":....,}
        """
        leg1 = instrument[leg]
        Day_Counter   = Day_Count.Day_Counter(leg1["day_convention"])
        currency      = leg1["currency"]
        convention    = self.convention[currency]
        cv_instrument = self.curve_instrument[currency]
        fx_instrument = self.cv_fx_instrument[currency]
        """ Discounting Curve settings below
        """
        if disc_cv_details["type"].upper() == "XCS":
            """ For XCS calculation we have to use 
                dual curves method libor curve for 
                coupon calculation and basis adjusted
                curve for discounting 
            """
            cv_dis = self.gen_swap_curve( value_date,
                                          convention,
                                          fx_instrument, 
                                          disc_cv_details,
                                          Day_Counter )
            disc_cv_details["type"] = "SWAP"
            cv_fwd = self.gen_swap_curve( value_date,
                                          convention,
                                          cv_instrument, 
                                          disc_cv_details,
                                          Day_Counter )
            disc_cv_details["type"] = "XCS"
        else:
            Day_Counter.set_convention_by_ccy(currency)
            cv_fwd = self.gen_swap_curve( value_date,
                                          convention,
                                          cv_instrument, 
                                          disc_cv_details,
                                          Day_Counter )
            
            cv_dis = cv_fwd
        cf_tb  = CF_Gen( leg1, 
                         cv_fwd,
                         self.cv_keeper,
                         Day_Counter )
        INT_flow = [[ele["End_Time"],ele["Interests"]] for ele in cf_tb]
        NPV_INT  = Tools.cal_npv( INT_flow, cv_dis, Day_Counter )
        PRI_flow = [[ele["End_Time"],ele["Principal"]] for ele in cf_tb]
        NPV_PRI  = Tools.cal_npv( PRI_flow, cv_dis, Day_Counter )
        return NPV_INT,NPV_PRI
        
        
        
    def gen_swap_curve( self,
                        value_date,
                        convention,
                        instrument,
                        disc_cv_details,
                        Day_Counter ):
        """ Wrapper function:
            Generate swap curve depends on 
            disc_cv_details is either 
            XCS or LIBOR
        """
        
        curve = B_S.boot_strapping_LIBOR( value_date, 
                                          convention,
                                          instrument, 
                                          Day_Counter )
        return curve
    def gen_zero_curve( self,
                        value_date,
                        convention,
                        instrument,
                        disc_cv_details,
                        Day_Counter ):
        """ Wrapper function:
            Generate swap curve depends on 
            disc_cv_details is either 
            XCS or LIBOR
        """
        curve = B_S.boot_strapping_Zero( value_date, 
                                         convention,
                                         instrument, 
                                         Day_Counter )
        return curve
        
    def gen_swap_instruments( self,
                              instrument ):
        """ generate swap instrument from 
            general instrument
        """
        swap_instrument = OrderedDict()
        leg1 = OrderedDict()
        leg1["currency"] = instrument["leg1_ccy"]
        leg1["acc_cpn_detail"] = instrument["leg1_cpn_detail"]
        leg1["pay_convention"] = instrument["leg1_pay_convention"]
        leg1["balance_tb"] = instrument["balance_tb_1"]
        leg1["day_convention"] = instrument["leg1_day_convention"]
        leg2 = OrderedDict()
        leg2["currency"] = instrument["leg2_ccy"]
        leg2["acc_cpn_detail"] = instrument["leg2_cpn_detail"]
        leg2["pay_convention"] = instrument["leg2_pay_convention"]
        leg2["balance_tb"] = instrument["balance_tb_2"]
        leg2["day_convention"] = instrument["leg2_day_convention"]
        swap_instrument["leg1"] = leg1
        swap_instrument["leg2"] = leg2
        return swap_instrument
    
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
        
    def to_string( self ):
        """ self.answer_bk is a dictionary with key = name
            value contains both valuetions and risks calculation
        """
        bk = self.answer_bk
        num = len([ele for ele in self.answer_bk.items()])
        
        key_str = "Swap Info:\n"
        key_str += "Current has: "+str(num) +" of Swaps.\n"
        key_str += "They are:\n"
        for name, val in self.instruments.items():
            ans = bk[name]
            key_str += name + ":\n"
            key_str += "###--- Values ---###\n"
            key_str += "NPV1="+str(ans["NPV1"]) + "\n"
            key_str += "NPV2="+str(ans["NPV2"]) + "\n"
            key_str += "NPV_Net="+str(ans["NPV_Net"]) + "\n"
            key_str += "###--- Risks ---###\n"
            key_str += "Net_PV01=" + str(ans["Net"]["PV01"]) +"\n"
            key_str += "####################\n"
        return key_str
    
    def get_answer( self ):
        return self.instruments, self.answer_bk




