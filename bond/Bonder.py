# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 14:12:45 2018

This is a bond object which can be used to handle 
all bond related requirements 

@author: Shaolun Du
@Contact: Saholun.du@gmail.com
"""

from collections import OrderedDict
import datetime as dt
import bond.bond_tools  as Tools
import bond.Day_Counter_func as Day_Count
from bond.Cash_Flow_Gen import CF_Gen as CF_Gen

class Bonder:
    def __init__( self,
                  cur_date,
                  Curve_Keeper ):
        """ Initial settings for swaper
            swap_instrument will contain all
            information needed to do pricing
            as well as risk analysis
            swap_instrument = { "name":....,
                                "leg1":....,
                                "leg2":... }
        """
        self.cur_date = cur_date
        
        self.curve_keeper = Curve_Keeper
        
        self.answer_bk = OrderedDict()
        self.instruments = OrderedDict()
        
    def add( self, 
             name, 
             instrument, 
             disc_cv_details ):
        instr = self.gen_bond_instruments( instrument )
        self.instruments[name] = [instr,disc_cv_details]
    
    def cal_bond( self, 
                  value_date ):
        """ Calculate all bond positions 
            valuation and risks
            NOTE: value_date can be different from 
                  cur_date which allows to value
                  bonds in future date
        """
        if isinstance( value_date, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
                try:
                    value_date = dt.datetime.strptime(value_date, fmt).date()
                    break
                except ValueError:
                    pass
        if len(self.instruments.items()) == 0:
            print("Get No Bonds Positions At ALL...")
            print("Return 0...")
            return 0
        for name, data in self.instruments.items():
            val_ans,cf_tb,delta_cf,fv_cf  = self.cal_npv_bond( value_date, 
                                                               data[0], 
                                                               data[1] )
            risk_ans = self.cal_risk_bond( value_date,
                                           data[0],
                                           data[1] )
            self.answer_bk[name] = {}
            self.answer_bk[name]["Type"] = "Bond"
            self.answer_bk[name]["Currency"] = data[0]["leg1"]["currency"]
            self.answer_bk[name]["Value"]    = val_ans
            self.answer_bk[name]["Risk"]     = risk_ans
            self.answer_bk[name]["CF_fv"]    = { "Net":fv_cf }
            self.answer_bk[name]["CF_delta"] = { "Net":delta_cf }
            self.answer_bk[name]["Schedule"] = { "Leg1":cf_tb,
                                                 "Leg2":[0] }
            
            
    def cal_npv_bond( self,
                      value_date,
                      instrument,
                      disc_cv_details ):
        answer = OrderedDict()
        npv1,cf_tb,delta_cf = self.cal_value_single( "leg1",
                                                     value_date,
                                                     instrument,
                                                     disc_cv_details )
        fv_cf = [[ele["End_Time"], ele["PMT"]] for ele in cf_tb if ele["End_Time"] >= value_date ]
        answer["NPV1"] = npv1
        answer["NPV_Net"] = npv1
        return answer,cf_tb,delta_cf, fv_cf
    
    def cal_risk_bond( self,
                       value_date,
                       instrument,
                       disc_cv_details ):
        answer = OrderedDict()
        """ answer is a dictionary of dictionaries 
            with risks values = {{leg1},{leg2},{Net}}
        """
        answer["leg1"] = self.cal_KRD_single( "leg1",
                                               value_date,
                                               instrument,
                                               disc_cv_details )
        net_bk = {}
        for key, val in answer["leg1"].items():
            net_bk[key] = val
        answer["Net"] = net_bk
        
        return answer
    
    def cal_value_single( self,
                          leg,
                          value_date,
                          instrument,
                          disc_cv_details ):
        Int_PMT = "PMT"
        """ disc_cv_details is the specification
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
        Day_Counter = Day_Count.Day_Counter(leg1["day_convention"])
        currency    = leg1["currency"]
        """ Discounting Curve settings below
        """
        spread  = disc_cv_details["spread"]*100 # units in %
        cv_dis = self.gen_bond_curve( currency, 
                                      -1, 
                                      0,
                                      spread,
                                      Day_Counter,
                                      disc_cv_details)
        cv_fwd = cv_dis
        
        cv_fwd = Tools.augument_by_frequency(cv_fwd, 1)
        cf_tb = CF_Gen( leg1, 
                        cv_fwd,
                        self.curve_keeper,
                        Day_Counter )
        cash_flow = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_tb]
        NPV = Tools.cal_npv( cash_flow, cv_dis )
        """ Shocking the curve by 100 bps and 
            calculate sensitivity on that 
        """
        cv_del = self.gen_bond_curve( currency, 
                                      0, 
                                      100,
                                      spread,
                                      Day_Counter,
                                      disc_cv_details)
        
        cv_del = Tools.augument_by_frequency(cv_del, 1)
        cf_del = CF_Gen( leg1, 
                        cv_del,
                        self.curve_keeper,
                        Day_Counter )
        cash_flow_del = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_del]
        delta_cf = [[e1[0],e1[1]-e2[1]] for e1,e2 in zip(cash_flow_del,cash_flow) if e1[0] >= value_date]

        return NPV,cf_tb,delta_cf
    
    

   
    def cal_KRD_single( self,
                        leg,
                        value_date,
                        instrument,
                        disc_cv_details ):
        Int_PMT = "PMT"
        risk_book = OrderedDict() # answer collactor
        """ This is the function to calculate all risks
            contains pv01,krd01,krd02,...,krd40
            CF changes when rates up 100bps
        """
        leg1    = instrument[leg]
        Day_Counter = Day_Count.Day_Counter(leg1["day_convention"])
        currency    = leg1["currency"]
        spread = disc_cv_details["spread"]*100
        """ Generate curves based on settings
        """
        cv_dis = self.gen_bond_curve( currency, 
                                      -1, 
                                      0,
                                      spread,
                                      Day_Counter,
                                      disc_cv_details )
        cv_fwd = cv_dis
        
        cv_fwd = Tools.augument_by_frequency(cv_fwd, 1)
        cf_tb = CF_Gen( leg1, 
                        cv_fwd,
                        self.curve_keeper,
                        Day_Counter )
        cash_flow = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_tb]
        NPV0 = Tools.cal_npv( cash_flow, cv_dis )
        """ Calculate pv01
        """
        BPS= 1
        cv_dis = self.gen_bond_curve( currency, 
                                      0, 
                                      BPS,
                                      spread,
                                      Day_Counter,
                                      disc_cv_details)
        
        cv_fwd = cv_dis
        cv_fwd = Tools.augument_by_frequency(cv_fwd, 1)
        cf_tb = CF_Gen( leg1, 
                        cv_fwd,
                        self.curve_keeper,
                        Day_Counter )
        cash_flow = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_tb]
        NPV1 = Tools.cal_npv( cash_flow, cv_dis )
        risk_book["PV01"] = NPV1-NPV0
        """ Calculate KRDs
        """
        years   = [1,2,3,5,7,10,15,20,25,30,40]
        ALL_KRD = []
        for y in range(1,42):
            cv_dis = self.gen_bond_curve( currency, 
                                          y, 
                                          BPS,
                                          spread,
                                          Day_Counter,
                                          disc_cv_details)
            
            cv_fwd = cv_dis
            cv_fwd = Tools.augument_by_frequency(cv_fwd, 1)
            cf_tb = CF_Gen( leg1, 
                            cv_fwd,
                            self.curve_keeper,
                            Day_Counter )
            cash_flow = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_tb]
            NPVs = Tools.cal_npv( cash_flow, cv_dis )
            ALL_KRD.append(NPVs-NPV0)
        KRD = [0 for i in range(len(years))]
        """ Loc is 1-40 corresponding to years
        """
        loc = 0
        for y_loc in range(1, len(years)):
            pre_y = years[y_loc-1]
            cur_y = years[y_loc]
            while loc <= cur_y:
                cur_KRD = ALL_KRD[loc]
                KRD[y_loc-1] += cur_KRD*(1-(loc-pre_y)/(cur_y-pre_y))
                KRD[y_loc]   += cur_KRD*(1-(cur_y-loc)/(cur_y-pre_y))
                loc += 1
        KRD[y_loc] += ALL_KRD[-1]
        for loc in range(len(KRD)):
            y   = years[loc]
            krd = KRD[loc] 
            if y < 10:
                risk_book["KRD0" + str(y)] = krd
            else:
                risk_book["KRD" + str(y)]  = krd
        return risk_book
    
    def gen_bond_curve( self,
                        currency, 
                        shock_year, 
                        BPS,
                        spread,
                        Day_Counter,
                        disc_cv_details ):
        """ Wrapper function:
            Generate bond curve depends on 
            disc_cv_details is either 
            XCS or LIBOR
        """
        cv_bk = self.curve_keeper.gen_curve(  currency, 
                                              shock_year, 
                                              BPS,
                                              spread,
                                              Day_Counter )
        cv = cv_bk["LIBOR"]
        
        return cv
        
    def gen_bond_instruments( self,
                              instrument ):
        """ generate bond instrument from 
            general instrument
        """
        bond_instrument = OrderedDict()
        leg1 = OrderedDict()
        leg1["currency"] = instrument["leg1_ccy"]
        leg1["acc_cpn_detail"] = instrument["leg1_cpn_detail"]
        leg1["pay_convention"] = instrument["leg1_pay_convention"]
        leg1["balance_tb"] = instrument["balance_tb_1"]
        leg1["day_convention"] = instrument["day_convention"]
        leg2 = OrderedDict()
        leg2["currency"] = instrument["leg2_ccy"]
        leg2["acc_cpn_detail"] = instrument["leg2_cpn_detail"]
        leg2["pay_convention"] = instrument["leg2_pay_convention"]
        leg2["balance_tb"] = instrument["balance_tb_2"]
        leg2["day_convention"] = instrument["day_convention"]
        bond_instrument["leg1"] = leg1
        bond_instrument["leg2"] = leg2
        return bond_instrument
      
        
    def to_string( self ):
        """ self.answer_bk is a dictionary with key = name
            value contains both valuetions and risks calculation
        """
        bk = self.answer_bk
        num = len([ele for ele in self.answer_bk.items()])
        
        key_str = "Bond Info:\n"
        key_str += "Current has: "+str(num) +" of Bonds.\n"
        key_str += "They are:\n"
        for name, val in self.instruments.items():
            ans = bk[name]
            key_str += name + ":\n"
            key_str += "###--- Values ---###\n"
            key_str += "NPV1="+str(ans["NPV1"]) + "\n"
            key_str += "NPV_Net="+str(ans["NPV_Net"]) + "\n"
            key_str += "###--- Risks ---###\n"
            key_str += "Net_PV01=" + str(ans["Net"]["PV01"]) +"\n"
            key_str += "####################\n"
        return key_str
    
    def get_answer( self ):
        return self.instruments, self.answer_bk


