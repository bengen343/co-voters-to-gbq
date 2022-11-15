import os
import zipfile

import pandas as pd

from config import *


def extract_co_voter_file():
    for file in os.listdir():
        if '.zip' in file:
            zip_ref = zipfile.ZipFile(file)
            zip_ref.extractall()
            zip_ref.close()

            os.remove(file)


def load_co_voter_file():
    files_lst = os.listdir()
    files_lst = [file for file in files_lst if 'voters' in file.lower()]
    _df = pd.DataFrame()
    _lst = []
    
    for file in files_lst:
        print(f"Loading file: {file}")
        _df = pd.read_csv(file, sep=",", encoding='cp437', index_col=None, header=0, low_memory=False, error_bad_lines=False)
        _lst.append(_df)
    
    voter_file_df = pd.concat(_lst)
    voter_file_df.reset_index(drop=True, inplace=True)

    for column in list(voter_file_df):
        if 'date' in column.lower():
            voter_file_df[column] = pd.to_datetime(voter_file_df[column], errors='coerce')
        elif column in integer_col_lst:
            voter_file_df[column] = voter_file_df[column].astype('float64').astype('Int64')
        else:
            voter_file_df[column] = voter_file_df[column].astype('str')

    print(f"Total Voters Loaded: {len(voter_file_df):,.0f}")
    return voter_file_df


# Load vote history dataframe with elections of interest
def vote_history_to_df(bq_query_str=bq_history_str):
    _df = pd.read_gbq(bq_query_str, project_id=bq_project_name, location=bq_project_location, credentials=bq_credentials, progress_bar_type='tqdm')
    print(f"Total Vote History Records: {len(_df):,.0f}")

    # Collapse history into single binary row
    _df = pd.get_dummies(_df.set_index('VOTER_ID')['ELECTION_DATE'])
    _df = _df.reset_index().groupby('VOTER_ID').sum()
    _df.reset_index(level=0, inplace=True)

    # Fix VOTER_ID datatype
    _df['VOTER_ID'] = _df['VOTER_ID'].astype('int64')

    # Reset column headings to strings
    columns_lst = list(_df)
    columns_lst = ['VOTER_ID'] + [x.date().strftime('%Y-%m-%d') for x in columns_lst[1:]]
    _df.columns = columns_lst

    return _df
