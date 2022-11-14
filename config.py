import json
import os
from datetime import date

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

bq_table_stem = bq_project_id + '.co_voterfile.'
bq_table_id = bq_table_stem + 'voters_' +str(date.today().year) + f"{(date.today().month - 1):02d}" + '01'

bq_history_str = '''
SELECT *
FROM `cpc-datawarehouse-51210.co_voterfile.vote-history`
WHERE ELECTION_DATE IN (''' + election_str + ''')
    OR ELECTION_DATE IS NULL'''

# Establish BigQuery credentials
bq_account_creds = json.loads(os.environ.get('BQ_ACCOUNT_CREDS'))
bq_credentials = service_account.Credentials.from_service_account_info(bq_account_creds)
