# -*- coding: utf-8 -*-
"""
Created on Thu Dec 4 08:49:51 2018
This is the main function to do 
swap pricing find out the corresponding
fixed rate of a given swap/XCS
Inputs:
    Live Pricing.xlsm contains tab:
        [ "Rate_Upload":    for LIBOR curve instruments,
          "FX_Curve_Upload":for Basis adjusted curve 
                            instruments,
          "FX_Upload":      for fx live spot rate,
          "Schedule":       a list of inputs swap positions 
                            for pricing
        ]
Outputs:
    fixed swap rate on leg2 (in default)
    Can be adjusted and out put all detailed cash flows
    
@author: Shaolun Du
@contacts: shaolun.du@gmail.com
"""
import os 
import xlwings as xw
from IO import Reader as reader
from Live_Pricing.SW_Pricer import Pricer as Pricer
from curve import Curve_Keeper as C_K
""" Set up enviroments
"""
dir_path = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__)))
f_name   = dir_path+"\\Live Pricing.xlsm"

fx_name  = "FX_Live"
balance_name = "Schedule"

""" Set up objects
"""
reader  = reader.excel_reader(f_name)

fx_spot = reader.read_FX_rates(fx_name)
source  = reader.read_source("Pricer")
""" Choose Pricing Source
"""
if "H" in source.upper():
    s_name    = "Rate_History"
    s_fx_name = "FX_Curve_History"
elif "L" in source.upper():
    s_name    = "Rate_Live"
    s_fx_name = "FX_Curve_Live"

cv_instrument    = reader.read_instruments(s_name, 8)
cv_fx_instrument = reader.read_instruments(s_fx_name, 8)

reader.read(balance_name)
name, raw_data  = reader.get_raw_data()

position_name   = name[0]
disc_cv_details = { "type" : raw_data[position_name]["itype"],
                    "spread" : 0 }

""" Start Pricing
"""
sheet_name = "Pricer"
val_date  = reader.read_value_date("Pricer")

curve_keeper = C_K.Curve_Keeper( "2018-11-30",
                                 "Yield_Curve" )
Pricer = Pricer( cv_instrument,
                 cv_fx_instrument,
                 fx_spot,
                 curve_keeper )
i_row,i_col = 13,1
sht = xw.Book.caller().sheets[sheet_name]
for name,value in raw_data.items():
    Pricer.add( name,
                raw_data[name],
                disc_cv_details )
    rts,npv = Pricer.price_swap( name,
                                 val_date )
    position = raw_data[name]
    sht.range((i_row,i_col),(i_row,i_col)).value = name
    sht.range((i_row,i_col+1),(i_row,i_col+1)).value = position["itype"]
    sht.range((i_row,i_col+2),(i_row,i_col+2)).value = str(val_date)
    ccy = position["leg1_ccy"]+":"+position["leg2_ccy"]
    sht.range((i_row,i_col+3),(i_row,i_col+3)).value = ccy
    sht.range((i_row,i_col+4),(i_row,i_col+4)).value = position["balance_tb_1"][0][1]
    sht.range((i_row,i_col+5),(i_row,i_col+5)).value = position["leg1_cpn_detail"][0][1]+":"+str(position["leg1_cpn_detail"][0][2])
    sht.range((i_row,i_col+6),(i_row,i_col+6)).value = position["leg2_cpn_detail"][0][1]+":"+str(position["leg2_cpn_detail"][0][2])
    sht.range((i_row,i_col+7),(i_row,i_col+7)).value = str(rts)
    sht.range((i_row,i_col+8),(i_row,i_col+8)).value = str(npv)
    i_row += 1









