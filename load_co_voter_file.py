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
    files_list = os.listdir()
    files_list = [file for file in files_list if 'voters' in file.lower()]
    _df = pd.DataFrame()
    _list = []
    
    for file in files_list:
        print(f"Loading file: {file}")
        _df = pd.read_csv(file, sep=",", encoding='cp437', index_col=None, header=0, low_memory=False, error_bad_lines=False)
        _list.append(_df)
    
    voter_file_df = pd.concat(_list)
    voter_file_df.reset_index(drop=True, inplace=True)
    voter_file_df['VOTER_ID'] =  voter_file_df['VOTER_ID'].astype('float').astype('int64')

    return voter_file_df

# Load vote history dataframe with elections of interest
def vote_history_to_df(bq_query_str=bq_history_str):
    _df = pd.read_gbq(bq_query_str, project_id=bq_project_id, location=bq_project_location, credentials=bq_credentials, progress_bar_type='tqdm')
    print(f"Total Vote History Records: {len(_df):.0f}")

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