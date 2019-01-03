# -*- coding: utf-8 -*-
"""
Created on Tue Nov 13 13:49:03 2018
This is a FX object which can be used to handle 
all FX related requirements 

@author: Shaolun Du
@Contacts:Shaolun.du@gmail.com
"""
from collections import OrderedDict
import fx.FX_Tools  as Tools
import datetime as dt
import fx.Day_Counter_func as Day_Count
from fx.Cash_Flow_Gen import CF_Gen as CF_Gen
import DB.dbExecute as dbEx

class FXer:
    def __init__( self,
                  cur_date,
                  curve_keeper ):
        """ Initial settings for fxer
            swap_instrument will contain all
            information needed to do pricing
            as well as risk analysis
            fx_instrument = { "name":....,
                                "leg1":....,
                                "leg2":... }
        """
        self.cur_date = cur_date
        self.curve_keeper = curve_keeper
        
        self.spot_rate = self.get_fx_spot_raw( "Yield_Curve" )
        
        self.answer_bk = OrderedDict()
        self.instruments = OrderedDict()
        
    def add( self, name, instrument, disc_cv_details ):
        instr = self.gen_fx_instruments( instrument )
        self.instruments[name] = [instr,disc_cv_details]
    
    def cal_fx( self, 
                value_date ):
        """ Calculate all fx positions 
            valuation and risks
            NOTE: value_date can be different from 
                  cur_date which allows to value
                  fx in future date
        """
        if isinstance( value_date, str ):
            for fmt in ( "%Y-%m-%d", "%m/%d/%Y" ):
                try:
                    value_date = dt.datetime.strptime(value_date, fmt).date()
                    break
                except ValueError:
                    pass
        if len(self.instruments.items()) == 0:
            print("Get No FX Positions At ALL...")
            print("Return 0...")
            return 0
        for name, data in self.instruments.items():
            val_ans,delta_net,fv_net,tb_1,tb_2  = self.cal_npv_fx( value_date, 
                                                                  data[0], 
                                                                  data[1] )
            risk_ans = self.cal_risk_fx( value_date,
                                         data[0],
                                         data[1] )
            self.answer_bk[name] = {}
            self.answer_bk[name]["Type"] = "FX"
            self.answer_bk[name]["Currency"] = { "Leg1":data[0]["leg1"]["currency"],
                                                 "Leg2":data[0]["leg2"]["currency"] }
            self.answer_bk[name]["Value"] = val_ans
            self.answer_bk[name]["Risk"] = risk_ans
            self.answer_bk[name]["CF_fv"] = { "Net":fv_net }
            self.answer_bk[name]["CF_delta"] = { "Net":delta_net }
            self.answer_bk[name]["Schedule"] = { "Leg1":tb_1,
                                                 "Leg2":tb_2 }
            
            
    def cal_npv_fx( self,
                    value_date,
                    instrument,
                    disc_cv_details ):
        answer = OrderedDict()
        print(disc_cv_details)
        print(instrument)
        npv1,tb_1,delta_1 = self.cal_value_single( "leg1",
                                                   value_date,
                                                   instrument,
                                                   disc_cv_details )
        npv2,tb_2,delta_2 = self.cal_value_single( "leg2",
                                                   value_date,
                                                   instrument,
                                                   disc_cv_details )
        
        cf_fv_1 = [[ele["End_Time"],ele["PMT"]] for ele in tb_1]
        cf_fv_2 = [[ele["End_Time"],ele["PMT"]] for ele in tb_2]
        
        if instrument["leg1"]["currency"] != instrument["leg2"]["currency"]:
            """ If two legs have different currency that means
                this is a XCS then we provide valuation in 
                leg1's currency
            """
            d_ccy = instrument["leg1"]["currency"]
            f_ccy = instrument["leg2"]["currency"]
            fx_rate = self.spot_rate[f_ccy]/self.spot_rate[d_ccy]
            
            cf_fv_2 = self.translate_cf( cf_fv_2,
                                         d_ccy,
                                         f_ccy,
                                         disc_cv_details,
                                         fx_rate )
        else:
            """ Same currency means this 
                is a normal swap
            """
            fx_rate = 1
        delta_net = [[cf_fv_1[0][0],0]]
        fv_net = [[e1[0],e1[1]-e2[1]] for e1,e2 in zip(cf_fv_1,cf_fv_2) if e1[0] >= value_date ]
        answer["NPV1"] = npv1
        answer["NPV2"] = npv2/fx_rate
        answer["NPV_Net"] = npv1-npv2/fx_rate

        return answer,delta_net,fv_net,tb_1,tb_2
    
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
        
        cv_dis = self.gen_fx_curve( currency, 
                                    -1, 
                                    0,
                                    spread,
                                    Day_Counter,
                                    disc_cv_details )
        
        cf_tb = CF_Gen( leg1,
                        cv_dis,
                        self.curve_keeper,
                        Day_Counter )
        cash_flow = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_tb]
        NPV = Tools.cal_npv( cash_flow, cv_dis )
        """ FX does not have rate sensitivity
        """
        cf_delta = [[cash_flow[0][0],0]]
        return NPV,cf_tb,cf_delta
    
    
    def cal_risk_fx( self,
                     value_date,
                     instrument,
                     disc_cv_details ):
        answer = OrderedDict()
        answer["leg1"] = self.cal_risk_single( "leg1",
                                               value_date,
                                               instrument,
                                               disc_cv_details )
        answer["leg2"] = self.cal_risk_single( "leg2",
                                               value_date,
                                               instrument,
                                               disc_cv_details )
        
        if instrument["leg1"]["currency"] != instrument["leg2"]["currency"]:
            """ If two legs have different currency that means
                this is a XCS then we provide valuation in 
                leg1's currency
            """
            d_ccy = instrument["leg1"]["currency"]
            f_ccy = instrument["leg2"]["currency"]
            fx_rate = self.spot_rate[f_ccy]/self.spot_rate[d_ccy]
        else:
            """ Same currency means this 
                is a normal swap
            """
            fx_rate = 1
        
        net_bk = {}
        for key, val in answer["leg1"].items():
            net_bk[key] = val - answer["leg2"][key]/fx_rate
        answer["Net"] = net_bk
        return answer
    
    def cal_risk_single( self,
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
        cv_dis = self.gen_fx_curve( currency, 
                                    -1, 
                                    0,
                                    spread,
                                    Day_Counter,
                                    disc_cv_details )
        cf_tb = CF_Gen( leg1, 
                        cv_dis,
                        self.curve_keeper,
                        Day_Counter )
        cash_flow = [[ele["End_Time"],ele[Int_PMT]] for ele in cf_tb]
        NPV0 = Tools.cal_npv( cash_flow, cv_dis )
        """ Calculate pv01
        """
        BPS= 1
        cv_dis = self.gen_fx_curve( currency, 
                                      0, 
                                      BPS,
                                      spread,
                                      Day_Counter,
                                      disc_cv_details)
        cf_tb = CF_Gen( leg1, 
                        cv_dis,
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
            cv_dis = self.gen_fx_curve( currency, 
                                          y, 
                                          BPS,
                                          spread,
                                          Day_Counter,
                                          disc_cv_details)
            cf_tb = CF_Gen( leg1, 
                            cv_dis,
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
    
    def translate_cf( self,
                      raw_cf,
                      raw_ccy,
                      target_ccy,
                      disc_cv_details,
                      fx0 ):
        """ Translate current cash flow table
            into target currency
        """
        Day_Counter = Day_Count.Day_Counter("30/360")
        spread = 0
        ans_cf = []
        f_cv = self.gen_fx_curve( target_ccy, 
                                  -1, 
                                  0,
                                  spread,
                                  Day_Counter,
                                  disc_cv_details )
        f_cv = Tools.augument_by_frequency(f_cv, 1)
        d_cv = self.gen_fx_curve( raw_ccy, 
                                  -1, 
                                  0,
                                  spread,
                                  Day_Counter,
                                  disc_cv_details )
        d_cv = Tools.augument_by_frequency(d_cv, 1)
        for ele in raw_cf:
            date = ele[0]
            cf = ele[1]
            fx_rate = fx0*self.get_fx_rate( date, f_cv, d_cv)
            ans_cf.append([date,cf/fx_rate])
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
            print("Cannot find date on curve...")
            print(date)
            return 0
        
        return d_df/f_df
    
    def gen_fx_curve( self,
                      currency, 
                      shock_year, 
                      BPS,
                      spread,
                      Day_Counter,
                      disc_cv_details ):
        cv_bk = self.curve_keeper.gen_curve(  currency, 
                                              shock_year, 
                                              BPS,
                                              spread,
                                              Day_Counter )

        cv = cv_bk["FX"]
        return cv
        
    def gen_fx_instruments( self,
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
        
        key_str = "FX Info:\n"
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