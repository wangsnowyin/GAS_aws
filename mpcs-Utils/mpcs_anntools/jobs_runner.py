from hashlib import sha1
import json, uuid, subprocess, boto3, datetime, base64, hmac, sys
import botocore.session, HTMLParser
import requests
from config import *


def main(argv=None):
    # Connect to SQS and get the message queue
    sqs = boto3.resource('sqs')
    sqs_queue_name = job_queue
    queue = sqs.get_queue_by_name(QueueName=sqs_queue_name)

    # Poll the message queue in a loop
    while True:

        # Attempt to read a message from the queue
        # Use long polling - DO NOT use sleep() to wait between polls
        messages = queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=20)

        # If no message was read, continue polling loop
        if len(messages) <= 0:
            continue
        # If a message was read, extract job parameters from the message body
        else:
            for message in messages:
                # Parse message and get parameters
                msg_body = eval(eval(message.body)['Message'])
                key = msg_body['s3_key_input_file']
                bucket = msg_body['s3_inputs_bucket']
                jobID = msg_body['job_id']
                usrname = msg_body['username']
                email = msg_body['email']
                s3file = msg_body['input_file_name']
                temp = s3file.split('~')
                filename = temp[1]
                filepath = "data/" + s3file

                print filepath
                s3_res = boto3.resource('s3')
                status = "RUNNING"
                cmd = 'python run.py {0} {1} {2} {3}'.format(filepath, jobID, usrname, email)

                try:
                    #download the task file from s3 bucket and launch it
                    s3_res.Bucket(bucket).download_file(key, filepath)
                    subprocess.Popen(cmd.split())
                except Exception, e:
                    status = "FAILED"
                    print e
                finally:
                    #persist the RUNNING status of a job
                    dynamodb = boto3.resource('dynamodb')
                    ann_table = dynamodb.Table(dynamo_table)
                    res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'status':{'Value':status, 'Action':'PUT'}})

                    # Delete the message from the queue
                    print ("Deleting message...")
                    message.delete()

if __name__ == "__main__":
    sys.exit(main())
