import os

import pandas as pd
from flask import Flask

import load_co_voter_file
import save_to_bq
import sos_fetch
from config import *

app = Flask(__name__)

@app.route('/')
def main():
    sos_fetch.sos_fetch()

    load_co_voter_file.extract_co_voter_file()
    print("Loading voter file")
    voter_file_df = load_co_voter_file.load_co_voter_file()

    print("Setting column datatypes")
    for column in list(voter_file_df):
        if 'DATE' in column:
            voter_file_df[column] = pd.to_datetime(voter_file_df[column], format='%m/%d/%Y', infer_datetime_format=True)
        else:
            voter_file_df[column] = voter_file_df[column].astype('str')
                
    print("Building schema")
    bq_schema_list = save_to_bq.create_bq_schema(_df=voter_file_df)
    print("Uploading to BigQuery")
    save_to_bq.save_to_bq(_df=voter_file_df, bq_table_schema=bq_schema_list, table_id=bq_table_id, project_id=bq_project_id)

    file_list = os.listdir()
    file_list = [file for file in file_list if '.txt' in file]

    for file in file_list:
        os.remove(file)

    return("CO voter file loaded to BigQuery successfully")

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)
    