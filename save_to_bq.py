import pandas as pd
from google.cloud import bigquery
from oauth2client.service_account import ServiceAccountCredentials

from config import *


def create_bq_schema(_df):
    schema_list = []
    for column in list(_df):
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


def save_to_bq(_df, bq_table_schema, table_id, project_id=bq_project_name):
    _df.to_gbq(destination_table=table_id, project_id=project_id, if_exists='replace', table_schema=bq_table_schema, credentials=bq_credentials)
