import json
import os
from datetime import date, timedelta

from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials

# FTP variables
ftp_address = 'ftps.sos.state.co.us'
ftp_directory = r'/EX-003 Master Voter List'

# Voter file variables
# Select elections of interest
generals_lst = ['2020-11-03', '2018-11-06', '2016-11-08', '2014-11-04']
primaries_lst = ['2020-06-30', '2018-06-26', '2016-06-28', '2014-06-24']

election_str = '\''
for election in (generals_lst + primaries_lst):
    election_str = election_str + '\', \'' + election
election_str = election_str + '\''
election_str = election_str[4:]

# BQ Variables
bq_project_id = os.environ.get('BQ_PROJECT_ID')
bq_project_location = 'us-west1'
bq_dataset_name = 'co_voterfile'
bq_table_name = f'{str((date.today() + timedelta(-30)).year)}{((date.today() + timedelta(-30)).month):02d}01'
bq_table_id = f'{bq_project_id}.{bq_dataset_name}.{bq_table_name}'

bq_history_str = '''
SELECT *
FROM `cpc-datawarehouse-51210.co_voterfile.vote-history`
WHERE ELECTION_DATE IN (''' + election_str + ''')
    OR ELECTION_DATE IS NULL'''

# Establish BigQuery credentials
bq_account_creds = json.loads(os.environ.get('BQ_ACCOUNT_CREDS'))
bq_credentials = service_account.Credentials.from_service_account_info(bq_account_creds)
