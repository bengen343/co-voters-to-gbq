import os
import zipfile

import numpy as np
import pandas as pd
from tqdm import tqdm

from config import *
from transform_co_voters import set_dtypes_on


def extract_co_voter_file():
    print("Unzipping constituent files...")
    for file in os.listdir():
        if '.zip' in file:
            zip_ref = zipfile.ZipFile(file)
            zip_ref.extractall()
            zip_ref.close()

            os.remove(file)


def load_co_voter_file(integer_col_lst, float_col_lst):
    print("Loading constituent files to dataframe...")
    files_lst = os.listdir()
    files_lst = [file for file in files_lst if 'registered_voters' in file.lower()]
    df = pd.DataFrame()
    lst = []
    
    for file in files_lst:
        print(f"Loading file: {file}")
        df = pd.read_csv(file, sep=',', encoding='cp437', index_col=None, header=0, low_memory=False, on_bad_lines='warn')
        lst.append(df)
    
    voter_file_df = pd.concat(lst)
    voter_file_df = voter_file_df[~voter_file_df['VOTER_ID'].isna()]
    voter_file_df.reset_index(drop=True, inplace=True)

    voter_file_df = set_dtypes_on(voter_file_df, voters_integer_cols_lst, voters_float_cols_lst)

    print(f"Total Voters Loaded: {len(voter_file_df):,.0f}")
    
    return voter_file_df


# Load vote history dataframe with elections of interest
def vote_history_to_df(bq_query_str=bq_history_query_str):
    print("Downloading vote history...")
    df = pd.read_gbq(bq_query_str, project_id=bq_project_name, location=bq_project_location, credentials=bq_credentials, progress_bar_type='tqdm')
    print(f"Total Vote History Records: {len(df):,.0f}")

    # Collapse history into single binary row
    df = pd.get_dummies(df.set_index('VOTER_ID')['ELECTION_DATE'])
    df = df.reset_index().groupby('VOTER_ID').sum()
    df.reset_index(level=0, inplace=True)

    # Fix VOTER_ID datatype
    df['VOTER_ID'] = df['VOTER_ID'].astype('int64')

    # Reset column headings to strings
    columns_lst = list(df)
    columns_lst = ['VOTER_ID'] + [x.strftime('%Y-%m-%d') for x in columns_lst[1:]]
    df.columns = columns_lst

    return df
