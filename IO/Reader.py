# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 16:37:13 2018
This is the function to read data from
excel 
@author: ACM05
"""
import xlrd
import IO.IO_Tools_Func as IO_TF
from collections import OrderedDict

class excel_reader():
    """ This is the excel reader take the 
        given structure
    """
    def __init__( self,
                  f_name ):
        self.f_name = f_name
        self.workbook = xlrd.open_workbook(self.f_name)
        self.raw_data = OrderedDict()
        
    def read( self,
              s_name ):
        """ read excel and parsing it by defined formating
        """
        col_num   = 1
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        num_rows  = worksheet.nrows - 1
        num_cols  = worksheet.ncols
        while col_num < num_cols:
            itype = worksheet.cell(0,col_num).value
            name = worksheet.cell(1,col_num).value
            leg1_ccy = worksheet.cell(2,col_num).value
            leg2_ccy = worksheet.cell(3,col_num).value
            leg1_cpn_detail = self.convert_2_list(worksheet.cell(4,col_num).value)
            leg2_cpn_detail = self.convert_2_list(worksheet.cell(5,col_num).value)
            
            leg1_pay_convention = self.convert_2_list(worksheet.cell(6,col_num).value)
            leg2_pay_convention = self.convert_2_list(worksheet.cell(7,col_num).value)
            
            day_convention = self.convert_2_list(worksheet.cell(8,col_num).value)
            balance_tb_1 = self.get_schedule( workbook,
                                              worksheet,
                                              11,
                                              col_num-1,
                                              num_rows)
            if itype.upper() in ("XCS","FX"):
                """ Read two more columns with difference 
                    notional table
                """
                col_num += 2
                balance_tb_2 = self.get_schedule( workbook,
                                                  worksheet,
                                                  11,
                                                  col_num-1,
                                                  num_rows )
            else:
                balance_tb_2 = balance_tb_1
                
            self.gen_instruments( itype,
                                  name,
                                  leg1_ccy,
                                  leg2_ccy,
                                  leg1_cpn_detail,
                                  leg2_cpn_detail,
                                  leg1_pay_convention,
                                  leg2_pay_convention,
                                  day_convention,
                                  balance_tb_1,
                                  balance_tb_2 )
            col_num += 3
    def read_value_date( self,
                         s_name ):
        """ Get corresponding value date
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        return xlrd.xldate.xldate_as_datetime(worksheet.cell(3,1).value, workbook.datemode).date()
    
    def read_source( self,
                     s_name ):
        """ Get corresponding BBG Source
            given sheet name
        """
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        return worksheet.cell(4,1).value
    
    def read_instruments( self,
                          s_name,
                          ccy_num ):
        """ Raed instuemtns from inputs excel 
            special to handle live data pricing
            Output is set of rates which will be feed
            into boot strapping
        """
        ans = {}
        i_row,i_col,t_row = 0,0,0
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        num_rows  = worksheet.nrows
        for i_row in range(ccy_num):
            Cash = []
            Future = [] 
            Swap = [] 
            i_col = 0
            currency = worksheet.cell(3+i_row*25,i_col).value
            num_cash = worksheet.cell(3+i_row*25,i_col+1).value
            fut_cash = worksheet.cell(3+i_row*25,i_col+3).value
            swp_cash = worksheet.cell(3+i_row*25,i_col+5).value
            t_row = 5+i_row*25
            while worksheet.cell(t_row,i_col).value != "":
                date = xlrd.xldate.xldate_as_datetime(worksheet.cell(t_row,i_col).value, workbook.datemode)
                rate = worksheet.cell(t_row,i_col+1).value
                Cash.append([date.date(),rate])
                t_row += 1
            t_row = 5+i_row*25
            i_col += 2
            while worksheet.cell(t_row,i_col).value != "":
                date = xlrd.xldate.xldate_as_datetime(worksheet.cell(t_row,i_col).value, workbook.datemode)
                rate = worksheet.cell(t_row,i_col+1).value
                Future.append([date.date(),rate])
                t_row += 1
            i_col += 2
            t_row = 5+i_row*25
            while worksheet.cell(t_row,i_col).value != "":
                date = xlrd.xldate.xldate_as_datetime(worksheet.cell(t_row,i_col).value, workbook.datemode)
                rate = worksheet.cell(t_row,i_col+1).value
                Swap.append([date.date(),rate])
                t_row += 1
                if t_row >= num_rows:
                    break
            ans[currency] = {}
            ans[currency]["cash"]   = [ Cash, int(num_cash) ]
            ans[currency]["future"] = [ Future, int(fut_cash) ]
            ans[currency]["swap"]   = [ Swap, int(swp_cash) ]
        return ans
    
    def read_FX_rates( self,
                       s_name ):
        """ read fx spot rates from excel
            s_name = sheet name
        """
        ans       = {}
        i_row     = 1
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        num_rows  = worksheet.nrows - 1
        while i_row <= num_rows:
            currency = worksheet.cell(i_row,1).value
            spot     = worksheet.cell(i_row,4).value
            ans[currency] = spot
            i_row += 1
        return ans
            
    def read_project( self,
                      s_name ):
        p_data = OrderedDict() 
        i_row = 0
        workbook  = self.workbook
        worksheet = workbook.sheet_by_name(s_name)
        num_rows  = worksheet.nrows
        while i_row < num_rows: 
            if worksheet.cell(i_row,0).value == "":
                break
            position_name = worksheet.cell(i_row,0).value
            project_name = worksheet.cell(i_row,1).value
            B_CPTY = worksheet.cell(i_row,2).value
            CG_CPTY = worksheet.cell(i_row,3).value
            p_data[position_name] = { "project_name":project_name,
                                      "B_CPTY":B_CPTY,
                                      "CG_CPTY":CG_CPTY }
            i_row += 1
        return p_data
    
    def gen_instruments( self, 
                         itype,
                         name,
                         leg1_ccy,
                         leg2_ccy,
                         leg1_cpn_detail,
                         leg2_cpn_detail,
                         leg1_pay_convention,
                         leg2_pay_convention,
                         day_convention,
                         balance_tb_1,
                         balance_tb_2 ):
        """ Resturcture raw data into swap 
            instrument structure
        """
        ibook = OrderedDict()
        ibook["itype"] = itype
        ibook["leg1_ccy"] = leg1_ccy
        ibook["leg2_ccy"] = leg2_ccy
        ibook["leg1_cpn_detail"] = leg1_cpn_detail
        ibook["leg2_cpn_detail"] = leg2_cpn_detail
        ibook["leg1_pay_convention"] = leg1_pay_convention
        ibook["leg2_pay_convention"] = leg2_pay_convention
        ibook["leg1_day_convention"] = day_convention[0][0]
        ibook["leg2_day_convention"] = day_convention[0][1]
        ibook["balance_tb_1"] = balance_tb_1
        ibook["balance_tb_2"] = balance_tb_2
        self.raw_data[name] = ibook
        
        
    
    def get_schedule( self,
                      wb,
                      worksheet,
                      s_row,
                      s_col,
                      num_row ):
        """ Generate full schedule given location
        """
        balance_tb = []
        for row in range(s_row,num_row+1):
            if worksheet.cell(row,s_col).value != "":
                dates = xlrd.xldate.xldate_as_datetime(worksheet.cell(row,s_col).value, wb.datemode)
                balance_tb.append([dates.date(),worksheet.cell(row,s_col+1).value])
            else:
                break
        return balance_tb
    
    def convert_2_list( self,
                        inputs ):
        inputs = inputs.split("$")
        ans = []
        for ele in inputs:
            ele = ele[1:-1]
            temp = ele.split(",")
            li = []
            for x in temp:
                x = IO_TF.is_num(x)
                li.append(x)
            ans.append(li)
        return ans
    
    def get_raw_data( self ):
        names = [ele[0] for ele in self.raw_data.items()]
        print("#############################################")
        print("###---Current Captures:"+str(len(names))+" items---###")
        print(names)
        print("#############################################")
        
        return names, self.raw_data
    
    def to_string( self ):
        ans = ""
        names = [ele[0] for ele in self.raw_data.items()]
        ans += "#############################################\n"
        ans += "###---Current Captures:"+str(len(names))+" items---###\n"
        ans += ";".join(names)
        ans += "\n#############################################\n"
        return ans
    

        







