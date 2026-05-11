## extract_excel_helper.py
# import
import openpyxl
import pandas as pd


def extract_xls_data(path):

    xls = pd.ExcelFile(path)

    xls_tbl = []
    for sheet in xls.sheet_names:
        xls_tbl.append(pd.read_excel(path, 
                           sheet_name = sheet))

    return xls_tbl


def extract_xls_format(path):
    """
    -> merged cells
    -> comments
    -> styles
    -> formulas
    -> positions
    """


    return 