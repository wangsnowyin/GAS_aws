import json, uuid, subprocess, boto3, datetime, base64, hmac, sys, time
import botocore.session, HTMLParser
import requests
import MySQLdb
from config import *

# reference: https://codedump.io/share/zroLEC5F1YR2/1/check-if-a-key-exists-in-a-bucket-in-s3-using-boto3
def isObjExist(obj):
    try:
        obj.load()
    except Exception, e:
        return False
    else:
        return True

def checkUserRole(username):
    # reference: http://mysql-python.sourceforge.net/MySQLdb.html
    try:
        conn = MySQLdb.connect(host=rds_host, user=rds_username, passwd=rds_pwd, db=rds_dbname, port=int(rds_port))
        dbcursor = conn.cursor()
        query = "SELECT * FROM users WHERE username=%s"
        dbcursor.execute(query, (username,))
        user = dbcursor.fetchone()
        dbcursor.close()
        role = user[1]
    except Exception as e:
        print e
        return "error"
    else:
        return role


def main(argv=None):
    # Connect to SQS and get the message queue
    sqs = boto3.resource('sqs')
    sqs_queue_name = glacier_queue
    queue = sqs.get_queue_by_name(QueueName=sqs_queue_name)

    # Poll the message queue in a loop
    while True:

        # Attempt to read a message from the queue
        messages = queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=20)

        # If no message was read, continue polling loop
        if len(messages) <= 0:
            continue
        # If a message was read, extract job parameters from the message body
        else:
            for message in messages:
                # Parse message and get parameters
                msg_body = eval(eval(message.body)['Message'])

                msgType = msg_body['type']
                jobID = msg_body['job_id']
                usrname = msg_body['username']
                res_file = msg_body['result_file']
                input_file = msg_body['input_file']
                status = msg_body['status']
                complete_time = msg_body['time']

                if msgType == "archive":
                    s3 = boto3.resource('s3')
                    old = s3.Object(res_bucket, key_prefix + res_file)

                    if checkUserRole(usrname) == premium_user:
                        message.delete()

                    elif (int(time.time()) - complete_time) > free_user_limit and isObjExist(old) and checkUserRole(usrname) == free_user:
                        # move the res file to gas-archive
                        # reference: http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Object.copy_from
                        arch_file = key_prefix + usrname + "#" + res_file                        
                        s3Object = s3.Object(arch_bucket, arch_file)
                        response = s3Object.copy_from(
                            ACL = default_acl,
                            CopySource = {
                                'Bucket': res_bucket,
                                'Key': key_prefix + res_file
                            }
                        )
		
                        response = old.delete()

                        # move the input file to gas-archive
                        arch_file = key_prefix + usrname + "#" + input_file
                        s3 = boto3.resource('s3')
                        s3Object = s3.Object(arch_bucket, arch_file)
                        response = s3Object.copy_from(
                            ACL = default_acl,
                            CopySource = {
                                'Bucket': input_bucket,
                                'Key': key_prefix + input_file
                            }
                        )
            
                        old = s3.Object(input_bucket, key_prefix + input_file)
                        response = old.delete()
		
                        status = "ARCHIVED"

                        # persist the ARCHIVED status of a job
                        dynamodb = boto3.resource('dynamodb')
                        ann_table = dynamodb.Table(dynamo_table)
                        res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'status':{'Value':status, 'Action':'PUT'}})

                        # Delete the message from the queue
                        print ("Deleting message...")
                        message.delete()

                elif msgType == "restore":

                    # reference: https://github.com/boto/boto3/issues/380
                    s3 = boto3.resource('s3')
                    obj = s3.Object(arch_bucket, res_file)

                    if not isObjExist(obj):
                        continue;

                    obj.reload()
                    restore = obj.restore

                    # move the files that are restored or has not archived
                    if obj.storage_class != 'GLACIER' or 'ongoing-request="false"' in restore:
                        arch_key = res_file
                        res_key = key_prefix + res_file.split("#")[1]

                        if(res_key[-9:] == "annot.vcf"):
                            newObj = s3.Object(res_bucket, res_key)
                        else:
                            newObj = s3.Object(input_bucket, res_key)                          
                        
                        response = newObj.copy_from(
                            ACL = default_acl,
                            CopySource = {
                                'Bucket': arch_bucket,
                                'Key': arch_key
                            }
                        )
                        response = obj.delete()  

                        # persist the COMPLETED status of a job
                        status = "COMPLETED"
                        dynamodb = boto3.resource('dynamodb')
                        ann_table = dynamodb.Table(dynamo_table)
                        jobID = res_file.split("#")[1].split("~")[0]
                        res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'status':{'Value':status, 'Action':'PUT'}})

                        # Delete the message from the queue
                        print ("Deleting message...")
                        message.delete()
                   

if __name__ == "__main__":
    sys.exit(main())
