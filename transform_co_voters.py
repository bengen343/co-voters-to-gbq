import re
from datetime import datetime

import numpy as np
import pandas as pd

from config import *


def set_dtypes_on(df: pd.DataFrame, integer_col_lst: list, float_col_lst: list) -> pd.DataFrame:
    print("Setting data types...")
    for column in list(df):
        if 'date' in column.lower():
            df[column] = pd.to_datetime(df[column], errors='coerce')
        elif column in integer_col_lst:
            df[column] = pd.to_numeric(df[column], errors='coerce')
            df[column] = df[column].astype('float64').astype('Int64')
        elif column in float_col_lst:
            df[column] = pd.to_numeric(df[column], errors='coerce')
            df[column] = df[column].astype('float64')
            df[column] = df[column].astype('str')
        else:
            df[column] = df[column].astype('str')
            
    df['PHONE_NUM'] = df['PHONE_NUM'].apply(lambda x: re.sub('[^0-9]', '', str(x)))
    df['PHONE_NUM'] = df['PHONE_NUM'].replace('', np.nan)

    df = df.replace('nan', np.nan)

    return df


#Calculate PVG scores for all voters in a dataframe
def calc_pv(df, generals_lst, primaries_lst):
    print("Calculating PVG & PVP values...")

    # Add columns for the propensity scores
    df['PVG'] = 0
    df['PVG'] = 0

    last_dt = pd.to_datetime(generals_lst[0])

    # Calculate PVG score and add that column
    df['PVG'] = np.where(df['REGISTRATION_DATE'] > last_dt, 
    5,
    df[generals_lst[0]] + df[generals_lst[1]] + df[generals_lst[2]] + df[generals_lst[3]])

    # Calculate PVP score and add that column
    df['PVP'] = np.where(df['REGISTRATION_DATE'] > last_dt, 
    5, 
    df[primaries_lst[0]] + df[primaries_lst[1]] + df[primaries_lst[2]] + df[primaries_lst[3]])

    # Clean and reformat the voter score results
    df[['PVG', 'PVP']] = df[['PVG', 'PVP']].fillna(0)
    
    df['PVG'] = 'PVG' + df['PVG'].astype('Int64').astype('str')
    df['PVG'] = df['PVG'].replace('PVG<NA>', np.nan)
    df['PVP'] = 'PVP' + df['PVP'].astype('Int64').astype('str')
    df['PVP'] = df['PVP'].replace('PVP<NA>', np.nan)

    return df

# Add age ranges to registration
def calc_age(df):
    print("Adding age ranges to registration...")

    df['AGE_RANGE'] = '0'
    df.loc[(datetime.now().year - df['BIRTH_YEAR']) >= 62, 'AGE_RANGE'] = '>62'
    df.loc[((datetime.now().year - df['BIRTH_YEAR']) < 62) & ((datetime.now().year - df['BIRTH_YEAR']) >= 55), 'AGE_RANGE'] = '55-61'
    df.loc[((datetime.now().year - df['BIRTH_YEAR']) < 55) & ((datetime.now().year - df['BIRTH_YEAR']) >= 45), 'AGE_RANGE'] = '45-54'
    df.loc[((datetime.now().year - df['BIRTH_YEAR']) < 45) & ((datetime.now().year - df['BIRTH_YEAR']) >= 35), 'AGE_RANGE'] = '35-44'
    df.loc[((datetime.now().year - df['BIRTH_YEAR']) < 35) & ((datetime.now().year - df['BIRTH_YEAR']) >= 25), 'AGE_RANGE'] = '25-34'
    df.loc[((datetime.now().year - df['BIRTH_YEAR']) < 25) & ((datetime.now().year - df['BIRTH_YEAR']) >= 18), 'AGE_RANGE'] = '18-24'

    return df

def calc_race(df):
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
    df = pd.merge(df, surnames_df, on='LAST_NAME', how='left')

    return df


