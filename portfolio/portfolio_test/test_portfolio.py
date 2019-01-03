# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 15:17:32 2018
This is a test function for Portfolio 
object
@author: Shaolun Du
@Contaact: Shaolun.du@gmail.com
"""
import time
import datetime as dt
import pandas as pd 
import IO.Reader as Reader
import portfolio.Portfolio as Portfolio
from IO import Writer as Writer
start = time.time()
""" Setup reader 
"""
f_name = "Test.xlsx"
s_name = [ "Swap" ]
#s_name = [ "FX" ]
report_currency = "LCL"
output_fname = "Answer.xlsx"
output_sname = "Result"
writer = Writer.Writer(output_fname)
writer.add_sheet(output_sname)


reader = Reader.excel_reader( f_name )
for sheet in s_name:
    reader.read(sheet)
    
""" Test on Portfolio Object
"""
curve_date = "2018-11-30"
val_date = "2018-11-30"

Port = Portfolio.Portfolio( curve_date,
                            reader )
Port.analysis( val_date )
fx_usd, sw_usd,bd_usd, sp_usd = Port.translate_to_ccy(report_currency)

usd_bk = {**fx_usd, **sw_usd, **bd_usd, **sp_usd}
future_cf,delta_cf,fx_cf,risks = Port.gen_result_tables(usd_bk)

""" Writting into excel uotput file
"""
i_row,i_col = 0,0
writer.write_ticker( output_sname,i_row,i_col,
                        "Result is shown in: "+report_currency)
i_row += 1
writer.write_ticker( output_sname,i_row,i_col,
                        "Value Date:"+val_date)
i_row += 1
writer.write_ticker( output_sname,i_row,i_col,
                        "Future Cash Flow")
i_row += 1
df = pd.DataFrame(future_cf)
df = df.set_index('Name')
df = df.fillna(0)
writer.write_df( i_row,i_col,
                 df,
                 output_sname )
i_row += (df.shape[0]+5)
writer.write_ticker( output_sname,i_row,i_col,
                    "Future Cash Flow when rates up 100bps")
i_row += 1
df = pd.DataFrame(delta_cf)
df = df.set_index('Name')
df = df.fillna(0)
writer.write_df( i_row,i_col,
                 df,
                 output_sname )
i_row += (df.shape[0]+5)

writer.write_ticker( output_sname,i_row,i_col,
                    "Future Cash Flow when currency up 100bps")
i_row += 1
df = pd.DataFrame(fx_cf)
df = df.set_index('Name')
df = df.fillna(0)
writer.write_df( i_row,i_col,
                 df,
                 output_sname )
i_row += (df.shape[0]+5)
writer.write_ticker( output_sname,i_row,i_col,
                    "MtM curve sensitivity")
i_row += 1
df = pd.DataFrame(risks)
df = df.set_index('Name')
df = df.fillna(0)
writer.write_df( i_row,i_col,
                 df,
                 output_sname )
i_row += (df.shape[0]+5)
writer.close()
end = time.time()
print(end - start)

