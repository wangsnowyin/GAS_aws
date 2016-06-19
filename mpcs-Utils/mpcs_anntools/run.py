import sys
import time
import driver
import requests
import os
from hashlib import sha1
import json, uuid, subprocess, boto3, datetime, base64, hmac, time
import botocore.session, HTMLParser
from config import *


# A rudimentary timer for coarse-grained profiling
class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print "Elapsed time: %f ms" % self.msecs

if __name__ == '__main__':
    # Call the AnnTools pipeline
    if len(sys.argv) > 1:
        jobID = sys.argv[2]
        input_file_name = sys.argv[1]
        username = sys.argv[3]
        email = sys.argv[4]

        with Timer() as t:
            driver.run(input_file_name, 'vcf')
        print "Total runtime: %s seconds" % t.secs

        # Add code here to save results and log files to S3 results bucket
        input_file_names = input_file_name[:-3]
        res_file = input_file_names + "annot.vcf"
        log_file = input_file_names + "vcf.count.log"
        log_val = key_prefix + log_file[5:]
        res_val = key_prefix + res_file[5:]

        # Upload the results file and log file
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(res_bucket)
        status = "COMPLETED"

        try:
            bucket.upload_file(res_file, res_val)
            bucket.upload_file(log_file, log_val)
        except Exception, e:
            status = "FAILED"
            print e
        finally:
            dynamodb = boto3.resource('dynamodb')
            ann_table = dynamodb.Table(dynamo_table)
            res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'status':{'Value':status, 'Action':'PUT'}})

            # publish a notification to the result topic after the job is complete or failed
            datas = {"job_id":jobID, "username":username, "email":email, "input_file_name":input_file_name, "status": status}
            sns = boto3.resource('sns')
            topic = sns.Topic(results_arn)
            response = topic.publish(
                Message=json.dumps(datas),
            )

            if status=="COMPLETED":             
                complete_time = int(time.time())
                res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'s3_results_bucket':{'Value':res_bucket, 'Action':'PUT'}})
                res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'s3_key_log_file':{'Value':log_val, 'Action':'PUT'}})
                res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'s3_key_result_file':{'Value':res_val, 'Action':'PUT'}})
                res = ann_table.update_item(Key={'job_id':jobID}, AttributeUpdates={'complete_time':{'Value':complete_time, 'Action':'PUT'}})

                # publish a msg to glacier queue about the complete time of annotation task
                content = {"job_id":jobID, "username":username, "time":complete_time, "result_file":res_file[5:], "input_file":input_file_name[5:], "status": status, "type":"archive"}
                sns = boto3.resource('sns')
                topic = sns.Topic(glacier_arn)
                response = topic.publish(
                    Message=json.dumps(content),
                )

                try:
                    # Clean up (delete) local job files
                    os.remove(res_file)
                    os.remove(log_file)
                    os.remove(input_file_name)
                except Exception, e:
                    print e
                
    else:
        print 'A valid .vcf file must be provided as input to this program.'
