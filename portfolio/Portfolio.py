# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 14:09:47 2018

@author: ACM05
"""
import datetime as dt
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import curve.Curve_Keeper as BS_CK
from fx.FXer import FXer as FXer
from swap.Swaper import Swaper as Swaper
from bond.Bonder import Bonder as Bonder
from special.SPer import SPer as SPer
from translate.Translater import translater as Trans


class Portfolio():
    def __init__( self,
                  cur_date,
                  reader ):
        """ Initialization set-ups
        """
        self.cur_date = cur_date
        self.reader = reader
        self.names,self.data = reader.get_raw_data()
        """ Curve keeper used for book keeping
            of all curves shared by all
            objects below
        """
        self.curve_keeper = BS_CK.Curve_Keeper( cur_date,
                                                "Yield_Curve" )
        """ Functioning objects each one is 
            responsible for its own 
            fucntioning and each one has its
            own corresponging tools files
        """
        self.swaper = Swaper( cur_date, self.curve_keeper )
        self.fxer   = FXer( cur_date, self.curve_keeper )
        self.bonder = Bonder( cur_date, self.curve_keeper )
        self.sper   = SPer( cur_date, self.curve_keeper )
        """ Translater based on reporting
            currency
        """
        self.translater = Trans( cur_date, self.curve_keeper )
    
    def analysis( self,
                  val_date ):
        """ Run analysis and get back results
        """
        names = self.names
        data  = self.data
        for name in names:
            target = data[name]
            """ Inputs some disc_cv_details 
                and value date 
            """
            i_type = target["itype"]
            """ Adding spread to 
                discounting curves
            """
            disc_cv_details = { "type"  : i_type,
                                "spread": 0 }
            if i_type.upper() == "FX":
                self.fxer.add( name,
                               target,
                               disc_cv_details )
            elif i_type.upper() in ("XCS","SWAP"):
                self.swaper.add( name,
                                 target,
                                 disc_cv_details )
            elif i_type.upper() == "BOND":
                self.bonder.add( name,
                                 target,
                                 disc_cv_details )
            else:
                self.sper.add( name,
                               target,
                               disc_cv_details )
            
        self.fxer.cal_fx( val_date )     
        self.swaper.cal_swap( val_date )
        self.bonder.cal_bond( val_date ) 
        self.sper.cal_sp( val_date )     
        fx_inst, fx_ans = self.fxer.get_answer()
        sw_inst, sw_ans = self.swaper.get_answer()
        bd_inst, bd_ans = self.bonder.get_answer()
        sp_inst, sp_ans = self.sper.get_answer()
        return fx_ans, sw_ans,bd_ans,sp_ans, names, data
    
    def translate_to_ccy( self,
                          report_ccy ):
        """ This is a portfolio level
            translation into any reporting currency
            of all data that are currently
            in this portfolio
        """
        fx_trans, sw_trans, bd_trans = 0, 0, 0
        fx_inst, fx_ans = self.fxer.get_answer()
        sw_inst, sw_ans = self.swaper.get_answer()
        bd_inst, bd_ans = self.bonder.get_answer()
        sp_inst, sp_ans = self.sper.get_answer()
        fx_trans = self.translater.translate_answer( fx_ans,
                                                     report_ccy )
        sw_trans = self.translater.translate_answer( sw_ans,
                                                     report_ccy )
        bd_trans = self.translater.translate_answer( bd_ans,
                                                     report_ccy )
        sp_trans = self.translater.translate_answer( sp_ans,
                                                     report_ccy )
        return fx_trans, sw_trans, bd_trans, sp_trans
    
    def gen_result_tables( self,
                           ans_book ):
        """ Generate result pandas tables
            after analysis is done
        """
        time_frequency = relativedelta( months = 12 )
        if type(self.cur_date) is str:
            sdate = dt.datetime.strptime(self.cur_date,"%Y-%m-%d")
            sdate = dt.date(sdate.year,12,31)
        future_cf = []
        delta_cf = []
        fx_cf = []
        risks = []
        box = [[sdate+(y-1)*time_frequency,0] for y in range(41)]
        for name,data in ans_book.items():
            temp = OrderedDict()
            temp["Name"] = name
            temp["Type"] = data["Type"]
            temp["Currency"] = data["Currency"]
            temp["NPV"] = data["Value"]["NPV_Net"]
            for y in range(40):
                temp[str(sdate+y*time_frequency)] = 0
            idx = 0
            for loc in range(1, len(box)):
                if idx >= len(data["CF_fv"]["Net"]):
                    break
                while box[loc][0] >= data["CF_fv"]["Net"][idx][0] and \
                    box[loc-1][0] < data["CF_fv"]["Net"][idx][0]:
                        temp[str(box[loc][0])] += data["CF_fv"]["Net"][idx][1]
                        idx += 1
                        if idx >= len(data["CF_fv"]["Net"]):
                            break
            future_cf.append(temp)
            
            temp = OrderedDict()
            temp["Name"] = name
            temp["Type"] = data["Type"]
            temp["Currency"] = data["Currency"]
            for y in range(40):
                temp[str(sdate+y*time_frequency)] = 0
            idx = 0
            for loc in range(1, len(box)):
                if idx >= len(data["CF_delta"]["Net"]):
                    break
                while box[loc][0] >= data["CF_delta"]["Net"][idx][0] and \
                    box[loc-1][0] < data["CF_delta"]["Net"][idx][0]:
                        temp[str(box[loc][0])] += data["CF_delta"]["Net"][idx][1]
                        idx += 1
                        if idx >= len(data["CF_delta"]["Net"]):
                            break
            delta_cf.append(temp)
            temp = OrderedDict()
            temp["Name"] = name
            temp["Type"] = data["Type"]
            temp["Currency"] = data["Currency"]
            for y in range(40):
                temp[str(sdate+y*time_frequency)] = 0
            idx = 0
            for loc in range(1, len(box)):
                if idx >= len(data["FX_fv"]["Net"]):
                    break
                while box[loc][0] >= data["FX_fv"]["Net"][idx][0] and \
                    box[loc-1][0] < data["FX_fv"]["Net"][idx][0]:
                        temp[str(box[loc][0])] += data["FX_fv"]["Net"][idx][1]
                        idx += 1
                        if idx >= len(data["FX_fv"]["Net"]):
                            break
            fx_cf.append(temp)
            temp = OrderedDict()
            temp["Name"] = name
            temp["Type"] = data["Type"]
            temp["Currency"] = data["Currency"]
            for key,val in data["Risk"]["Net"].items():
                temp[key] = val
            risks.append(temp)
        return future_cf,delta_cf,fx_cf,risks
            
    def gen_scott_filed( self,
                         val_date ):
        """ Special function to generate
            related fileds as scott needs
        """
        p_data = self.reader.read_project("Projects")
        ans_li = []
        fx_ans, sw_ans,bd_ans, names, data = self.analysis( val_date )
        ans = {**fx_ans, **sw_ans }
        for name in names:
            if name in p_data:
                leg1_cpn = data[name]["leg1_cpn_detail"][0]
                leg2_cpn = data[name]["leg2_cpn_detail"][0]
                cpn = ""
                if len(leg1_cpn) >= 2:
                    if leg1_cpn[1].upper() == "FIX":
                        cpn += str(int(leg1_cpn[2]*10000)/100) + "%:"
                    else:
                        cpn += leg1_cpn[2] + "L:"
                if len(leg2_cpn) >= 2:
                    if leg2_cpn[1].upper() == "FIX":
                        cpn += str(int(leg2_cpn[2]*10000)/100) + "%"
                    else:
                        cpn += leg2_cpn[2] + "L"
             
                ans_book = OrderedDict()
                ans_book["Project"] = p_data[name]["project_name"]
                ans_book["Name"] = name
                ans_book["Bank"] = p_data[name]["B_CPTY"]
                ans_book["Type"] = data[name]["itype"]
                ans_book["Coupon"] = cpn
                ans_book["Notional"] = data[name]["balance_tb_1"][0][1]
                ans_book["Start Date"] = data[name]["balance_tb_1"][0][0]
                ans_book["End Date"] = data[name]["balance_tb_1"][-1][0]
                ans_book["Value Date"] = val_date
                ans_book["NPV"] = ans[name]["Value"]["NPV_Net"]
                ans_book["PV01"] = ans[name]["Risk"]["Net"]["PV01"]
                ans_li.append(ans_book)
        return ans_li
        
        
    
        
    
        
        
        
        
        
    