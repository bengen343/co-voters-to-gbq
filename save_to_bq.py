import pandas as pd
from google.cloud import bigquery
from oauth2client.service_account import ServiceAccountCredentials

from config import *


def create_bq_schema(df, integer_col_lst):
    schema_list = []
    for column in list(df):
        if 'date' in column.lower():
            sql_type = 'DATE'
        elif column in integer_col_lst:
            sql_type = 'INT64'
        else:
            sql_type = 'STRING'
                
        if column == 'VOTER_ID':
            sql_mode = 'REQUIRED'
        else:
            sql_mode = 'NULLABLE'
            
        schema_list.append({'name':  column, 'type': sql_type, 'mode': sql_mode})
    
    return schema_list
