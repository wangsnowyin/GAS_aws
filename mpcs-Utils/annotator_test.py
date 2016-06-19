import random, time, sys, json
import boto3

def main(argv=None):
	while True:
		jobid = "1b8bd949-4d82-41aa-9792-0f2586d10f0e"
		username = "abc"
		usermail = "328543041@qq.com"
		bucket = "gas-input"
		key = "xueyin/" + jobid + "~test.vcf"
		filename = key.split("/")[1]
		data = {"job_id":jobid, "username":username,"email":usermail, "submit_time":int(time.time()), "s3_inputs_bucket":bucket, "s3_key_input_file":key, "input_file_name":filename, "status":"PENDING"}

		#publish a notification to SNS topic
		sns = boto3.resource('sns')
		topic = sns.Topic('arn:aws:sns:us-east-1:127134666975:xueyin_job_notifications')
		response = topic.publish(
			Message=json.dumps(data),
		)

		time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())