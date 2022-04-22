import json
import os
from datetime import date

from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials

# FTP variables
ftp_address = 'ftps.sos.state.co.us'
ftp_directory = r'/EX-003 Master Voter List'

# BQ Variables
bq_project_id = os.environ.get('BQ_PROJECT_ID')

bq_table_stem = bq_project_id + '.co_voterfile.'
bq_table_id = bq_table_stem + str(date.today().year) + '-' f"{date.today().month:02d}"

# Establish BigQuery credentials
bq_account_creds = json.loads(os.environ.get('BQ_ACCOUNT_CREDS'))
bq_credentials = service_account.Credentials.from_service_account_info(bq_account_creds)
