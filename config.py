import json
import os
from datetime import date, timedelta

from google.oauth2 import service_account
#from oauth2client.service_account import ServiceAccountCredentials

# FTP variables
# Secret variables
ftp_user = os.environ.get('FTP_USER')
ftp_pass = os.environ.get('FTP_PASS')
ftp_address = 'ftps.sos.state.co.us'
ftp_directory = r'/EX-003 Master Voter List'

# Voter file variables
# Select elections of interest
generals_lst = ['2022-11-08', '2020-11-03', '2018-11-06', '2016-11-08', '2014-11-04']
primaries_lst = ['2022-06-28', '2020-06-30', '2018-06-26', '2016-06-28']

election_str = '\''
for election in (generals_lst + primaries_lst):
    election_str = election_str + '\', \'' + election
election_str = election_str + '\''
election_str = election_str[4:]

# BQ Variables
bq_project_name = os.environ.get('BQ_PROJECT_ID')
bq_project_location = 'us-west1'
bq_dataset_name = 'co_voterfile'
bq_voters_table_name = 'voters'
bq_new_voters_table_name = 'new-voters'
bq_voters_table_id = f'{bq_project_name}.{bq_dataset_name}.{bq_voters_table_name}'
bq_new_voters_table_id = f'{bq_project_name}.{bq_dataset_name}.{bq_new_voters_table_name}'


bq_history_query_str = '''
    SELECT
        *
    FROM `cpc-datawarehouse-51210.co_voterfile.vote-history`
    WHERE ELECTION_DATE IN (''' + election_str + ''')
        OR ELECTION_DATE IS NULL
'''

# Establish BigQuery credentials
bq_account_creds = json.loads(os.environ.get('BQ_ACCOUNT_CREDS'))
bq_credentials = service_account.Credentials.from_service_account_info(bq_account_creds)

# Data type variables
voters_integer_cols_lst = [
    'VOTER_ID',
    'COUNTY_CODE',
    'PRECINCT_NAME',
    'ADDRESS_LIBRARY_ID',
    'HOUSE_NUM',
    'RESIDENTIAL_ZIP_CODE',
    'RESIDENTIAL_ZIP_PLUS',
    'BIRTH_YEAR',
    'PRECINCT',
    'VOTER_STATUS_ID',
    'MAILING_ZIP_CODE',
    'MAILING_ZIP_PLUS'
]