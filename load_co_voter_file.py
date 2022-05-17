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
    files_list = [file for file in files_list if '.txt' in file]
    _df = pd.DataFrame()
    _list = []
    
    for file in files_list:
        _df = pd.read_csv(file, sep=",", encoding='cp437', index_col=None, header=0, low_memory=False, error_bad_lines=False)
        _list.append(_df)
    
    voter_file_df = pd.concat(_list)
    voter_file_df.reset_index(drop=True, inplace=True)
    del voter_file_df['backcall==0.2.0']

    return voter_file_df
