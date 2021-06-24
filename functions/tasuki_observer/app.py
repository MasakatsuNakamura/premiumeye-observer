import logging
import json
import base64
import gzip
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
  sns_topic_arn = os.environ['EMAIL_SNS_TOPIC_ARN']  # 環境変数よりSNSトピックARN取得
  sns_client = boto3.client('sns')

  # CloudWatchLogsからのデータはbase64エンコードされているのでデコード
  decoded_data = base64.b64decode(event['awslogs']['data'])
  # バイナリに圧縮されているため展開
  json_data = json.loads(gzip.decompress(decoded_data))

  logger.info("EVENT: " + json.dumps(json_data))

  # ログデータ取得
  message = json_data['logEvents'][0]['message']

  # SNS件名設定
  log_group = json_data['logGroup']
  log_stream = json_data['logStream']
  #ロググループ名、ログストリーム名をsubjectに設定
  subject = log_group + ' ' + log_stream

  sns_client.publish(
    TopicArn = sns_topic_arn,
    Subject = subject,
    Message = json.dumps(message)
  )
