import os
import time

import pandas as pd
from flask import Flask
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from config import *
from load_co_voter_file import (extract_co_voter_file, load_co_voter_file,
                                vote_history_to_df)
from save_to_bq import create_bq_schema
from sos_fetch import sos_dir_fetch
from transform_co_voters import calc_age, calc_pv, calc_race

app = Flask(__name__)

@app.route('/')
def main():
    # Download all the files that make up the master voter list from
    # the Colorado Secretary of State FTP.
    sos_dir_fetch(ftp_user, ftp_pass, ftp_address, ftp_directory)

    # Unzip all of the voter list files.
    extract_co_voter_file()

    # Load voter list files into dataframe.
    voter_file_df = load_co_voter_file(voters_integer_cols_lst)

    # Set the list of columns that will ultimately be uploaded to BigQuery.
    # This is all of the columns in the original file as well as those we're adding.
    voters_cols_lst = list(voter_file_df) + ['PVG', 'PVP', 'AGE_RANGE', 'RACE', 'VALID_FROM_DATE', 'VALID_TO_DATE']

    # Load vote history so we can calculate voters turnout propensity.
    vote_history_df = vote_history_to_df(bq_query_str=bq_history_query_str)
    voter_file_df = pd.merge(voter_file_df, vote_history_df, how='left', on='VOTER_ID')

    # Augment the voter registration data with additional demographic information.
    print("Calculating additional data fields...")
    voter_file_df = calc_pv(voter_file_df, generals_lst, primaries_lst)
    voter_file_df = calc_age(voter_file_df)
    voter_file_df = calc_race(voter_file_df)
    voter_file_df['VALID_FROM_DATE'] = None
    voter_file_df['VALID_TO_DATE'] = None
    voter_file_df = voter_file_df[voters_cols_lst]

    # Prepare to upload the data to BigQuery by checking if we're updating or creating a table.
    bq_client = bigquery.Client(credentials=bq_credentials)
    try:
        bq_table = bq_client.get_table(bq_voters_table_id)
        is_existing = True
    except NotFound:
        is_existing = False

    if is_existing is False:
        print("Incremental table doesn't exist yet, creating for the first time...")
        
        # Set the VALID_FROM_DATE to the last action for each voter recorded by the Secretary of State.
        voter_file_df['VALID_FROM_DATE'] = voter_file_df[['REGISTRATION_DATE', 'PARTY_AFFILIATION_DATE', 'EFFECTIVE_DATE']].max(axis=1)
        
        bq_schema_lst = create_bq_schema(voter_file_df, voters_integer_cols_lst)

        # Create the table in BigQuery and assign the column to partition on.
        incremental_table = bigquery.Table(bq_voters_table_id, schema=bq_schema_lst)
        incremental_table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.MONTH,
            field = 'VALID_TO_DATE'
        )
        incremental_table = bq_client.create_table(incremental_table)

        # Upload the data to start the incremental table.
        voter_file_df.to_gbq(destination_table=bq_voters_table_id, project_id=bq_project_name, if_exists='append', table_schema=bq_schema_lst, credentials=bq_credentials)
    
    elif is_existing is True:
        print("Incremental table exists, uploading temp table of new voters...")

        # Set the VALID_FROM_DATE to the last action for each voter recorded by the Secretary of State or the beginning of the prior month.
        voter_file_df['VALID_FROM_DATE'] = voter_file_df[['REGISTRATION_DATE', 'PARTY_AFFILIATION_DATE', 'EFFECTIVE_DATE']].max(axis=1)
        voter_file_df['VALID_FROM_DATE'] = voter_file_df['VALID_FROM_DATE'].apply(lambda x: max(x.date(), date((date.today() + timedelta(-30)).year, (date.today() + timedelta(-30)).month, 1)))

        # Some data points get deprecated over time. For any columns that aren't contained in new data add empty columns.
        bq_existing_cols_lst = [col.name for col in bq_table.schema]
        voters_missing_cols_lst = [col for col in bq_existing_cols_lst if col not in list(voter_file_df)]
        bq_missing_cols_lst = [col for col in list(voter_file_df) if col not in bq_existing_cols_lst]
        if len(bq_missing_cols_lst) > 0:
            return f"BigQuery requires the addtional columns: {bq_missing_cols_lst}"
        for col in voters_missing_cols_lst:
            voter_file_df[col] = None
        voter_file_df = voter_file_df[bq_existing_cols_lst]

        bq_schema_lst = create_bq_schema(voter_file_df, voters_integer_cols_lst)
        voter_file_df.to_gbq(destination_table=bq_new_voters_table_id, project_id=bq_project_name, if_exists='replace', table_schema=bq_schema_lst, credentials=bq_credentials)

        # Compose a SQL Query to compare the new and incremental tables and sunset the incremental records that have changed.
        bq_sunset_query_str = f'''
        SELECT
            COUNT(VOTER_ID)
        WHERE (VOTER_ID IN (SELECT VOTER_ID FROM (SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_voters_table_id}` WHERE VALID_TO_DATE IS NULL EXCEPT DISTINCT SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_new_voters_table_id}`))) AND VALID_TO_DATE IS NULL
        '''
        bq_result = bq_client.query(bq_sunset_query_str)
        print(f"Sunsetting {next(bq_result.result())[0]:,.0f} existing records that have changed...")
        
        bq_sunset_query_str = f'''
        UPDATE `{bq_voters_table_id}`
        SET VALID_TO_DATE = DATE(EXTRACT(YEAR FROM CURRENT_DATE()), EXTRACT(MONTH FROM CURRENT_DATE()), 1)
        WHERE (VOTER_ID IN (SELECT VOTER_ID FROM (SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_voters_table_id}` WHERE VALID_TO_DATE IS NULL EXCEPT DISTINCT SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_new_voters_table_id}`))) AND VALID_TO_DATE IS NULL
        '''
        # Run the SQL query to sunset incremental records that have changed or been erased in the latest update
        bq_sunset_job = bq_client.query(bq_sunset_query_str)
        time.sleep(120)

        # Compose a SQL Query to compare the new and incremental tables and add the new records.
        bq_add_query_str = f'''
        SELECT
            COUNT(updated.VOTER_ID)
        FROM ((SELECT VOTER_ID FROM (SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_new_voters_table_id}` EXCEPT DISTINCT SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_voters_table_id}` WHERE VALID_TO_DATE IS NULL)) AS ids
        LEFT JOIN `{bq_new_voters_table_id}` AS updated ON ids.VOTER_ID=updated.VOTER_ID)
        '''
        bq_result = bq_client.query(bq_sunset_query_str)
        print(f"Adding {next(bq_result.result())[0]:,.0f} new records to table...")
        
        bq_add_query_str = f'''
        INSERT `{bq_voters_table_id}`
        SELECT
            updated.*
        FROM ((SELECT VOTER_ID FROM (SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_new_voters_table_id}` EXCEPT DISTINCT SELECT * EXCEPT(VALID_FROM_DATE, VALID_TO_DATE) FROM `{bq_voters_table_id}` WHERE VALID_TO_DATE IS NULL)) AS ids
        LEFT JOIN `{bq_new_voters_table_id}` AS updated ON ids.VOTER_ID=updated.VOTER_ID)
        '''
        # Run the SQL query to add new records from the latest update.
        bq_add_job = bq_client.query(bq_add_query_str)
        time.sleep(120)
       
        # Delete the temporary new voters table.
        print("Cleaning up temporary BigQuery tables...")
        bq_client.delete_table(bq_new_voters_table_id, not_found_ok=True)

    # Remove voter file text files from drive.
    print("Cleaning up hard disk...")
    file_lst = os.listdir()
    file_lst = [file for file in file_lst if '.txt' in file]

    for file in file_lst:
        os.remove(file)

    return("CO voter file loaded to BigQuery successfully.")

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)
    