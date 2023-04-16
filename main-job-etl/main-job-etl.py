#import python libraries

import pandas as pd
import numpy as np
import datetime
from dateutil import parser
import boto3
import io
# import upload_csv


s3 = boto3.resource('s3')

bucket_name = 'tm-csv-bucket'
key_source = 'raw_data/dailycheckins.csv'
key_dest = 'cleaned_data/dailycheckins_cleaned.csv'

obj = s3.Object(bucket_name, key_source)
body = obj.get()['Body']


# define an empty DataFrame
df = pd.DataFrame()

# read the CSV file from S3 into the DataFrame
df = pd.read_csv(body)

# analyze data first
df.head()
df.tail()
df.describe()
df.dtypes


# set timestamp for index so we can facilitate time-based plotting
df.set_index('timestamp')

# check for missing datas, in this case i already know that some users are missing

missing_user = df['user'].isna()

missing_user_rows = df.loc[missing_user]

# print(missing_user_rows)

# after browsing through datas, it seems that some of months in the timestamp are in Russian String e.g апреля -> should be april
# creating a dictionary that maps the russian month to eng counterpart.

# Define a function to convert the timestamp string

# Define the mapping of Russian month names to English equivalents

# Define the mapping of Russian month names to English equivalents
ru_to_en = {
    'января': 'January',
    'февраля': 'February',
    'марта': 'March',
    'апреля': 'April',
    'мая': 'May',
    'июня': 'June',
    'июля': 'July',
    'августа': 'August',
    'сентября': 'September',
    'октября': 'October',
    'ноября': 'November',
    'декабря': 'December'
}



# Loop over each row in the dataframe
for i, row in df.iterrows():
    # Extract the timestamp from the row
    timestamp = row['timestamp']
    
    # Replace Russian month names with their English equivalents
    for ru, en in ru_to_en.items():
        timestamp = timestamp.replace(ru, en)
        
    # Parse the timestamp using dateutil.parser.parse()
    parsed_timestamp = parser.parse(timestamp)
    
    # Convert to the desired format
    formatted_timestamp = parsed_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
    
    # Update the dataframe with the formatted timestamp
    df.at[i, 'timestamp'] = formatted_timestamp

# Print the updated dataframe
print(df)

# df.to_csv('final.csv', sep='\t', encoding='utf-8')


# create a buffer to hold the CSV data
csv_buffer = io.StringIO()
df.to_csv(csv_buffer, sep='\t', encoding='utf-8', index=False)

# create a byte string from the buffer
csv_bytes = csv_buffer.getvalue().encode('utf-8')

# upload the file to S3 with SSE-S3 encryption
try:
    response = s3.Bucket(bucket_name).put_object(
        Key=key_dest,
        Body=csv_bytes,
        ServerSideEncryption='AES256'
    )


    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f"Error uploading file to S3: {response['ResponseMetadata']['HTTPStatusCode']}")
except Exception as e:
    print(str(e))
# upload_csv