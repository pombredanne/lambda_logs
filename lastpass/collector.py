from __future__ import print_function

import json
from datetime import datetime, timedelta

import boto3
import requests

API_END_POINT = 'https://lastpass.com/enterpriseapi.php'

# Your gonna need your keys for this - read the docs
API_KEY = 'FIXME'
API_CLIENT_ID = 'FIXME'

TO_DATE = datetime.today()

# This configures the pull for 15 minutes of data. To tune this, change the delta
FROM_DATE = TO_DATE - timedelta(seconds=900)

FORMATTED_TO_DATE = TO_DATE.strftime("%Y-%m-%d %H:%M:%S")
FORMATTED_FROM_DATE = FROM_DATE.strftime("%Y-%m-%d %H:%M:%S")

API_REQUEST_DATA = {
    "cid": API_CLIENT_ID,
    "provhash": API_KEY,
    "cmd": "reporting",
    "data":
        {
            "from": FORMATTED_FROM_DATE,
            "to": FORMATTED_TO_DATE,
            "user": "allusers",
            "format": "siem"
        }

}

API_REQUEST_HEADERS = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}

API_REQUEST_DATA_JSON = json.dumps(API_REQUEST_DATA)

S3 = boto3.resource('s3')

# The name of your S3 bucket... you can change this to whatever you want
S3_BUCKET_NAME = 'lastpass-logs'

LOG_FILE_NAME = 'lastpass_logs_' + str(datetime.now())


def upload_to_s3(data):
    '''Uploads the log file to the named s3 bucket
    '''
    try:
        siem_data = ""
        # Lastpass doesn't really like humans so we have to do some formatting
        for item, value in data.items():
            for event in value:
                siem_data += json.dumps(event) + "\n"

        # Upload to S3
        S3.Bucket(S3_BUCKET_NAME).put_object(Key=LOG_FILE_NAME, Body=siem_data)
    except Exception as ex:
        print('Failed to upload to s3 bucket :: ' + S3_BUCKET_NAME)
        raise


def lambda_handler(event, context):
    ''' The main lambda handler... this is the function called by aws
    '''
    print('Collecting logs from {} at {}...'.format(API_END_POINT, FORMATTED_TO_DATE))
    try:
        response = requests.post(API_END_POINT, data=API_REQUEST_DATA_JSON, headers=API_REQUEST_HEADERS)
        upload_to_s3(response.json())
    except:
        # Yep this is probably the worst and least helpful error message ever
        print('API request for lastpass logs failed')
        raise
    finally:
        print('Log collection complete at {}'.format(str(datetime.now())))
