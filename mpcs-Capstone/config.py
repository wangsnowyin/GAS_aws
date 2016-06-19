import ConfigParser

config = ConfigParser.ConfigParser()
config.read('mpcs.conf')
publish_key = config.get("mpcs.stripe", "public_key")
secret_key = config.get("mpcs.stripe", "secret_key")

free_user = config.get("mpcs.plans", "free")
premium_user = config.get("mpcs.plans", "premium")
email_addr = config.get("mpcs.auth", "email_sender")

res_bucket = config.get("mpcs.aws.s3", "results_bucket")
input_bucket = config.get("mpcs.aws.s3", "inputs_bucket")
arch_bucket = config.get("mpcs.aws.s3", "archive_bucket")
default_acl = config.get("mpcs.aws.s3", "default_acl")

glacier_queue = config.get("mpcs.aws.sqs", "glacier_queue")
job_queue = config.get("mpcs.aws.sqs", "job_queue")
results_queue = config.get("mpcs.aws.sqs", "results_queue")

glacier_arn = config.get("mpcs.aws.sns", "glacier_arn")
job_arn = config.get("mpcs.aws.sns", "job_arn")
results_arn = config.get("mpcs.aws.sns", "results_arn")

rds_host = config.get("mpcs.aws.rds", "rds_host")
rds_username = config.get("mpcs.aws.rds", "rds_username")
rds_pwd = config.get("mpcs.aws.rds", "rds_pwd")
rds_dbname = config.get("mpcs.aws.rds", "rds_dbname")
rds_port = config.get("mpcs.aws.rds", "rds_port")

dynamo_table = config.get("mpcs.aws.dynamodb", "dynamo_table")

key_prefix = config.get("mpcs.web", "key_prefix")
web_url = config.get("mpcs.web", "web_url")
free_user_limit = config.get("mpcs.web", "free_user_limit")
