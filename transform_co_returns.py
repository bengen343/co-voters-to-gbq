from datetime import datetime

import numpy as np
import pandas as pd

from config import *


#Calculate PVG scores for all voters in a dataframe
def calc_pv(_df, generals_lst=generals_lst, primaries_lst=primaries_lst):
    print("Calculating PVG & PVP values")

    # Clean data - fix date formatting, add new columnts
    _df['PVG'] = 0
    _df['PVG'] = 0

    last_dt = pd.to_datetime(generals_lst[0])

    # Calculate PVG score and add that column
    _df['PVG'] = np.where(_df['REGISTRATION_DATE'] > last_dt, 
    5,
    _df[generals_lst[0]] + _df[generals_lst[1]] + _df[generals_lst[2]] + _df[generals_lst[3]])

    # Calculate PVP score and add that column
    _df['PVP'] = np.where(_df['REGISTRATION_DATE'] > last_dt, 
    5, 
    _df[primaries_lst[0]] + _df[primaries_lst[1]] + _df[primaries_lst[2]] + _df[primaries_lst[3]])

    # Clean and reformat the voter score results
    _df[['PVG', 'PVP']].fillna(0, inplace=True)
    
    _df['PVG'] = 'PVG' + _df['PVG'].astype('Int64').astype('str')
    _df['PVP'] = 'PVP' + _df['PVP'].astype('Int64').astype('str')

    return _df

# Add age ranges to registration
def calc_age(_df):
    print("Adding age ranges to registration...")

    _df['AGE_RANGE'] = '0'
    _df.loc[(datetime.now().year - _df['BIRTH_YEAR']) >= 62, 'AGE_RANGE'] = '>62'
    _df.loc[((datetime.now().year - _df['BIRTH_YEAR']) < 62) & ((datetime.now().year - _df['BIRTH_YEAR']) >= 55), 'AGE_RANGE'] = '55-61'
    _df.loc[((datetime.now().year - _df['BIRTH_YEAR']) < 55) & ((datetime.now().year - _df['BIRTH_YEAR']) >= 45), 'AGE_RANGE'] = '45-54'
    _df.loc[((datetime.now().year - _df['BIRTH_YEAR']) < 45) & ((datetime.now().year - _df['BIRTH_YEAR']) >= 35), 'AGE_RANGE'] = '35-44'
    _df.loc[((datetime.now().year - _df['BIRTH_YEAR']) < 35) & ((datetime.now().year - _df['BIRTH_YEAR']) >= 25), 'AGE_RANGE'] = '25-34'
    _df.loc[((datetime.now().year - _df['BIRTH_YEAR']) < 25) & ((datetime.now().year - _df['BIRTH_YEAR']) >= 18), 'AGE_RANGE'] = '18-24'

    return _df

def calc_race(_df):
    # Add race classifier
    print("Applying race classifier...")
    
    # Import Census Surname List
    surnames_df = pd.DataFrame()
    surnames_df = pd.read_csv('Names_2010Census.csv', sep=',', encoding='cp437', index_col=None, header=0, low_memory=False)

    # Convert percentages from strings to numbers
    surnames_df['pctwhite'] = pd.to_numeric(surnames_df['pctwhite'], errors='coerce')
    surnames_df['pcthispanic'] = pd.to_numeric(surnames_df['pcthispanic'], errors='coerce')
    surnames_df['pctblack'] = pd.to_numeric(surnames_df['pctblack'], errors='coerce')
    surnames_df['pctapi'] = pd.to_numeric(surnames_df['pctapi'], errors='coerce')

    # Assign a race classification where probability is over 80%
    surnames_df['RACE'] = 'norace'
    surnames_df.loc[surnames_df['pcthispanic'] >= 80, 'RACE'] = 'Hispanic'
    surnames_df.loc[surnames_df['pctblack'] >= 80, 'RACE'] = 'Black'
    surnames_df.loc[surnames_df['pctapi'] >= 80, 'RACE'] = 'Asian'
    surnames_df.loc[surnames_df['pctwhite'] >= 80, 'RACE'] = 'White'
    
    # Purge irrelevant columns from surnames
    surnames_df = surnames_df[['name','RACE']]
    surnames_df.rename(columns={'name':'LAST_NAME'}, inplace=True)

    # Join surnames to given dataframe
    _df = pd.merge(_df, surnames_df, on='LAST_NAME', how='left')

    return _df


