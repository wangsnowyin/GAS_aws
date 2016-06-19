from hashlib import sha1
import json, uuid, subprocess, boto3, datetime, base64, hmac, sys
import botocore.session, HTMLParser
import requests
from config import *


def main(argv=None):
    # Connect to SQS and get the message queue
    sqs = boto3.resource('sqs')
    sqs_queue_name = results_queue
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
                
                #key = msg_body['s3_key_input_file']
                jobID = msg_body['job_id']
                usrname = msg_body['username']
                s3file = msg_body['input_file_name']
                status = msg_body['status']

                #send email to user informing status of the job when it finishes
                client = boto3.client('ses')
                f = open('email_result.tpl', 'r+')
                body = f.read()
                body = body.replace("username", usrname)
                body = body.replace("jobID", jobID)
                body = body.encode('UTF-8')
                toAddr = msg_body['email']

                # reference: http://boto3.readthedocs.io/en/latest/reference/services/ses.html#SES.Client.send_email
                response = client.send_email(
                    Source=email_addr,
                    Destination={
                        'ToAddresses': [
                        toAddr,
                        ]
                    },

                    Message={
                        'Subject': {
                        'Data': '[GAS]Status Inform for Your Job',
                        'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': body ,
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                )

                # Delete the message from the queue
                print ("Deleting message...")
                message.delete()

if __name__ == "__main__":
    sys.exit(main())


        

