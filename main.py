import os

import pandas as pd
from flask import Flask

from config import *
from load_co_voter_file import (extract_co_voter_file, load_co_voter_file,
                                vote_history_to_df)
from save_to_bq import create_bq_schema, save_to_bq
from sos_fetch import sos_dir_fetch
from transform_co_returns import calc_age, calc_pv, calc_race

app = Flask(__name__)

@app.route('/')
def main():
    # Download all the files that make up the master voter list from
    # the Colorado Secretary of State FTP.
    sos_dir_fetch()

    # Unzip all of the voter list files.
    extract_co_voter_file()

    # Load voter list files into dataframe.
    print("Loading voter file")
    voter_file_df = load_co_voter_file()

    # Set the list of columns that will ultimately be uploaded to BigQuery.
    column_lst = list(voter_file_df) + ['PVG', 'PVP', 'AGE_RANGE', 'RACE']

    print("Loading vote history.")
    vote_history_df = vote_history_to_df(bq_query_str=bq_history_str)

    # Match the various data sources together
    voter_file_df = pd.merge(voter_file_df, vote_history_df, how='left', on='VOTER_ID')

    # Augment the voter registration data with additional demographic information
    print("Calculating additional data fields.")
    voter_file_df = calc_pv(voter_file_df, generals_lst=generals_lst, primaries_lst=primaries_lst)
    voter_file_df = calc_age(voter_file_df)
    voter_file_df = calc_race(voter_file_df)

    voter_file_df = voter_file_df[column_lst]
                
    print("Building schema")
    bq_schema_lst = create_bq_schema(_df=voter_file_df)

    print("Uploading to BigQuery")
    save_to_bq(_df=voter_file_df, bq_table_schema=bq_schema_lst, table_id=bq_voters_table_id, project_id=bq_project_name)

    file_lst = os.listdir()
    file_lst = [file for file in file_lst if '.txt' in file]

    for file in file_lst:
        os.remove(file)

    return("CO voter file loaded to BigQuery successfully")

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)
    