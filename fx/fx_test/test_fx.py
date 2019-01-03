# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 10:21:34 2018
Test function for swap object

@author: Shaolun Du
@Contacts: Shaolun.du@gmail.com
"""
import pandas as pd
import fx.FXer as FXer
import curve.Curve_Keeper as CK
from collections import OrderedDict
from datetime import datetime

name = "Test" 
cur_date = "2018-11-29"
curve_keeper = CK.Curve_Keeper( cur_date, 
                                "Yield_Curve" )
fxer = FXer.FXer( cur_date, 
                  curve_keeper )

instrument = OrderedDict()
instrument["leg1_ccy"] = "USD"
instrument["leg1_cpn_detail"] = [[1000,"Fix",0,0,-100,100]]
instrument["leg1_pay_convention"] = [[1000,"6M"]]

instrument["balance_tb_1"] = [["9/4/2018",12595955],
                              ["12/18/2022",0] ]
for ele in instrument["balance_tb_1"]:
    ele[0] = datetime.strptime(ele[0],"%m/%d/%Y").date()
    
instrument["leg2_ccy"] = "BRL"
instrument["leg2_cpn_detail"] = [[1000,"Fix",0,0,-100,100]]
instrument["leg2_pay_convention"] = [[1000,"6M"]]
instrument["balance_tb_2"] = [ ["9/4/2018",53000000],
                               ["12/18/2022",0] ]
for ele in instrument["balance_tb_2"]:
    ele[0] = datetime.strptime(ele[0],"%m/%d/%Y").date()
instrument["day_convention"] = "ACT/360"

disc_cv_details = { "type"  : "FX",
                    "spread": 0 }

fxer.add( name, instrument, disc_cv_details )

fxer.cal_fx( cur_date )

ans = fxer.answer_bk
for key,val in ans.items():  
    print("Name of Position:")
    print(key)
    for k,v in val.items():
        print(k)
        print(v)
