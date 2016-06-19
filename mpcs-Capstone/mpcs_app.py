# Copyright (C) 2015 University of Chicago
#
import base64
import datetime
import hashlib
import hmac
import json
import sha
import string
import time
import urllib
import urlparse
import uuid
import boto3
import botocore.session
from boto3.dynamodb.conditions import Key

from mpcs_utils import log, auth
from bottle import route, request, redirect, template, static_file, run, HTTPError, error
from hashlib import sha1
import json, uuid, subprocess, boto3, datetime, base64, hmac, time
import botocore.session, HTMLParser
from boto3.dynamodb.conditions import Key, Attr
from config import *

'''
*******************************************************************************
Check whether login user to request
*******************************************************************************
'''
def check_connection(auth):
	WAIT_TIME = 0.5
	while True:
		try:
			temp = len(auth._store.users)
		except Exception, e:
			time.sleep(WAIT_TIME)
			continue
		else:
			break

def check_auth(request):
	auth.require(fail_redirect='/login?redirect_url=' + request.url)


'''
*******************************************************************************
Set up static resource handler - DO NOT CHANGE THIS METHOD IN ANY WAY
*******************************************************************************
'''
@route('/static/<filename:path>', method='GET', name="static")
def serve_static(filename):
	# Tell Bottle where static files should be served from
	return static_file(filename, root=request.app.config['mpcs.env.static_root'])

'''
*******************************************************************************
Home page
*******************************************************************************
'''
@route('/', method='GET', name="home")
def home_page():
	log.info(request.url)
	check_connection(auth)
	return template(request.app.config['mpcs.env.templates'] + 'home', auth=auth)

'''
*******************************************************************************
Registration form
*******************************************************************************
'''
@route('/register', method='GET', name="register")
def register():
	log.info(request.url)
	check_connection(auth)
	return template(request.app.config['mpcs.env.templates'] + 'register',
		auth=auth, name="", email="", username="", alert=False)

@route('/register', method='POST', name="register_submit")
def register_submit():
	check_connection(auth)
	auth.register(description=request.POST.get('name').strip(),
		username=request.POST.get('username').strip(),
		password=request.POST.get('password').strip(),
		email_addr=request.POST.get('email_address').strip(),
		role="free_user")
	return template(request.app.config['mpcs.env.templates'] + 'register', auth=auth, alert=True)

@route('/register/<reg_code>', method='GET', name="register_confirm")
def register_confirm(reg_code):
	log.info(request.url)
	check_connection(auth)
	auth.validate_registration(reg_code)
	return template(request.app.config['mpcs.env.templates'] + 'register_confirm', auth=auth)

'''
*******************************************************************************
Login, logout, and password reset forms
*******************************************************************************
'''
@route('/login', method='GET', name="login")
def login():
	log.info(request.url)
	check_connection(auth)
	redirect_url = "/annotations"
	# If the user is trying to access a protected URL, go there after auhtenticating
	if request.query.redirect_url.strip() != "":
		redirect_url = request.query.redirect_url

	return template(request.app.config['mpcs.env.templates'] + 'login', 
		auth=auth, redirect_url=redirect_url, alert=False)

@route('/login', method='POST', name="login_submit")
def login_submit():
	check_connection(auth)
	auth.login(
		request.POST.get('username'),
		request.POST.get('password'),
		success_redirect=request.POST.get('redirect_url'),
		fail_redirect='/login'
	)

@route('/logout', method='GET', name="logout")
def logout():
	check_connection(auth)
	auth.require(fail_redirect='/login')
	log.info(request.url)
	auth.logout(success_redirect='/login')


'''
*******************************************************************************
Core GAS code is below...
*******************************************************************************
'''

'''
*******************************************************************************
Subscription management handlers
*******************************************************************************
'''
import stripe

# Display form to get subscriber credit card info
@route('/subscribe', method='GET', name="subscribe")
def subscribe():
	check_connection(auth)
	check_auth(request)	
  	return template(request.app.config['mpcs.env.templates'] + 'subscribe', auth=auth)

# Process the subscription request
@route('/subscribe', method='POST', name="subscribe_submit")
def subscribe_submit():
	check_connection(auth)
	check_auth(request)	

	try:
		stripe.api_key = secret_key
  		token = request.forms.get('stripe_token')
		customer = stripe.Customer.create(
  			card = token,
 	 		plan = "premium_plan",
  			email = auth.current_user.email_addr,
  			description = auth.current_user.username
		)
	except Exception, e:
		print e
		return HTTPError(500, e)
	
	# update user role in db
	auth.current_user.update(role="premium_user")
	
	# restore data
	# reference: https://github.com/boto/boto3/issues/380
	username = auth.current_user.username
	s3 = boto3.resource('s3')
	bucket = s3.Bucket(arch_bucket)
	objs = bucket.objects.filter(Prefix = key_prefix)
	for obj in objs:
		if obj.key.split("#")[0] == key_prefix + username:

			if obj.storage_class == 'GLACIER' and obj.restore is None:
				resp = obj.restore_object(
					RequestPayer='requester',
					RestoreRequest={'Days': 1}
				)

			content = {"job_id":"", "username":username, "time":int(time.time()), "result_file":obj.key, "input_file":"", "status": "COMPLETED", "type":"restore"}
			sns = boto3.resource('sns')
			topic = sns.Topic(glacier_arn)
			response = topic.publish(
				Message=json.dumps(content),
			)
		
	return template(request.app.config['mpcs.env.templates'] + 'subscribe_confirm', auth=auth, stripe_id=customer['id'])

'''
*******************************************************************************
Display the user's profile with subscription link for Free users
*******************************************************************************
'''
@route('/profile', method='GET', name="profile")
def user_profile():
	check_connection(auth)
	check_auth(request)	
  	return template(request.app.config['mpcs.env.templates'] + 'profile', auth=auth)


'''
*******************************************************************************
Creates the necessary AWS S3 policy document and renders a form for
uploading an input file using the policy document
*******************************************************************************
'''
@route('/annotate', method='GET', name="annotate")
def upload_input_file():
	check_connection(auth)
	check_auth(request)	
  	AWS_ACCESS_KEY = botocore.session.Session().get_credentials().access_key
	AWS_SECRET_KEY = botocore.session.Session().get_credentials().secret_key
	expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=(5))
	expire = expires.strftime("%Y-%m-%dT%H:%M:%S.000Z")
	bucket = input_bucket
	acl = default_acl
	key_name = key_prefix
	redirect = web_url + "backfrom_upload"
	str_to_sign = '{"expiration":"%s","conditions":[{"bucket":"%s"}, ["starts-with","$key","%s"],{"acl":"%s"},' \
                  '{"success_action_redirect":"%s"}]}' % (expire, bucket,key_name, acl, redirect)

	# Encode and sign policy document
	base_64 = base64.b64encode(str_to_sign.encode('utf8'))
	signature = base64.b64encode(hmac.new(AWS_SECRET_KEY.encode(), base_64,sha1).digest())
	jobid = str(uuid.uuid4())
	# Render the upload form
	return template(request.app.config['mpcs.env.templates'] + 'upload', bucket_name=bucket, aws_acl=acl, job=jobid, aws_redirect=redirect, aws_key=AWS_ACCESS_KEY, aws_sig=signature, aws_policy=base_64, auth=auth)


'''
*******************************************************************************
Accepts the S3 redirect GET request, parses it to extract 
required info, saves a job item to the database, and then
publishes a notification for the annotator service.
*******************************************************************************
'''
@route('/backfrom_upload', method=['GET'])
def redirect_from_upload():
	check_connection(auth)
	# Get bucket name and key from the S3 redirect URL
	key = request.query.key
	bucket = request.query.bucket
	filename = key.split('/')[1]
	print key

	# get the unique job ID
	temp = filename.split('~')
	jobid = temp[0]

	# Create a job item and persist it to the annotations database
	username = auth.current_user.username
	usermail = auth.current_user.email_addr
	data = {"job_id":jobid, "username":username,"email":usermail, "submit_time":int(time.time()), "s3_inputs_bucket":bucket, "s3_key_input_file":key, "input_file_name":filename, "status":"PENDING"}
	dynamodb = boto3.resource('dynamodb')
	ann_table = dynamodb.Table(dynamo_table)
	ann_table.put_item(Item=data)

	#publish a notification to SNS topic
	#reference: http://boto3.readthedocs.io/en/latest/reference/services/sns.html#topic
	sns = boto3.resource('sns')
	topic = sns.Topic(job_arn)
	response = topic.publish(
		Message=json.dumps(data),
	)

	return template(request.app.config['mpcs.env.templates'] + 'upload_confirm.tpl', job_id=jobid, auth=auth)


'''
*******************************************************************************
List all annotations for the user
*******************************************************************************
'''
@route('/annotations', method='GET', name="annotations_list")
def get_annotations_list():
	check_connection(auth)
	check_auth(request)	
  	dynamodb = boto3.resource('dynamodb')
  	table = dynamodb.Table(dynamo_table)
	username = auth.current_user.username

	# reference: http://docs.aws.amazon.com/amazondynamodb/latest/gettingstartedguide/GettingStarted.Python.04.html
	response = table.query(
		IndexName='username-index',
       	KeyConditionExpression=Key('username').eq(username)
	)

  	return template(request.app.config['mpcs.env.templates'] + 'my_annotations', db_items=response, auth=auth)


'''
*******************************************************************************
Display details of a specific annotation job
*******************************************************************************
'''
@route('/annotations/<job_id>', method='GET', name="annotation_details")
def get_annotation_details(job_id):
	check_connection(auth)
	check_auth(request)	
	dynamodb = boto3.resource('dynamodb')

	try:
		table = dynamodb.Table(dynamo_table) 
		response = table.query(
			KeyConditionExpression=Key('job_id').eq(job_id)
		)
	except Exception, e:
		return HTTPError(404, e)

	return template(request.app.config['mpcs.env.templates'] + 'job_detail', item_info=response, auth=auth)

'''
*******************************************************************************
Download the result file for an annotation job
*******************************************************************************
'''
@route('/download/<filename>', method='GET')
def download_result(filename):
	check_connection(auth)
	check_auth(request)	
	input_file_names = filename[:-3]
	res_file = input_file_names + "annot.vcf"
	log_file = input_file_names + "vcf.count.log"
	
	# download file from s3 to server
	s3 = boto3.resource('s3')
	bucket = res_bucket
	path = "data/" + res_file		
	key = key_prefix + res_file
	try: 
		s3.Bucket(bucket).download_file(key, path)
	except Exception, e:
		return HTTPError(404, e)
	
	# reference:http://bottlepy.org/docs/dev/tutorial.html#static-files
	# download file from server to user laptop
	return static_file(path, root='', download=key)

'''
*******************************************************************************
Display the log file for an annotation job
*******************************************************************************
'''
@route('/annotations/<job_id>/log', method='GET', name="annotation_log")
def view_annotation_log(job_id):
	check_connection(auth)
	check_auth(request)	
  	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(dynamo_table)

	try:
		response = table.query(
			KeyConditionExpression=Key('job_id').eq(job_id)
		)

		for item in response['Items']:	
			log_file = item['s3_key_log_file']

		# download file from s3 to server
		s3 = boto3.resource('s3')
		bucket = res_bucket
		path = "data/" + log_file[6:]
		s3.Bucket(bucket).download_file(log_file, path)
	except Exception, e:
		return HTTPError(404, e)

		# download the log file
	return static_file(path, root='', download=log_file)

@route('/annotations/<job_id>/view_log', method='GET')
def view_annotation_log(job_id):
	check_connection(auth)
	check_auth(request)	
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(dynamo_table)

	try:
		response = table.query(
			KeyConditionExpression=Key('job_id').eq(job_id)
		)

		for item in response['Items']:
			log_file = item['s3_key_log_file']
		print log_file

		# reference: http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Object.get
		s3 = boto3.resource('s3')
		obj = s3.Object(res_bucket, log_file)
		log_data = obj.get()['Body'].read()
		log_data = log_data.replace("\n", '<br/>')

	except Exception, e:
		return HTTPError(404, e)

   	 # return the log file
	return log_data


'''
*******************************************************************************
Code to deal with HTTP erroes
*******************************************************************************
'''
# reference: http://bottlepy.org/docs/dev/tutorial.html#error-pages
# reference: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
def my_handler(code, msg, error):
	return template(request.app.config['mpcs.env.templates'] + 'error_page', code=code, msg=msg, error=error, auth=auth)

@error(404)
def error404(error):
	msg = "   Resource Not Found"
	return my_handler(404, msg, error)

@error(500)
def error500(error):
	msg = "   Internal Server Error"
	return my_handler(500, msg, error)


### EOF

