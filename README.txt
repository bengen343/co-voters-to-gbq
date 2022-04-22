This code sets up a Google Cloud Run service that will periodically download the complete voter
file from your Colorado Secretary of State FTP account and store it as a monthly table in your
Google BigQuery data warehouse.

You'll need to update varibles in config.py

# FTP variables
ftp_address = 'ftps.sos.state.co.us'
ftp_directory = r'/EX-003 Master Voter List'

# BQ Variables
bq_project_id: str
The Google Cloud project ID where your BigQuery warehouse resides

bq_table_stem: str
The dataset identifier in BigQuery. For example 'bq-datawarehouse.co_voterfile.'

This also relies on several environment variables to utilize your secrets

FTP_USER: str
Your Colorado Secretary of State FTP login

FTP_PASS: str
Your Colorado Secretary of State FTP password

BQ_ACCOUNT_CREDS: str
The full contents of your Google Service Account key JSON file as a single line of text
