import logging
import json
import base64
import gzip
import boto3
import os
import urllib.request

def slack_webhook_url(product_name):
  ssm = boto3.client('ssm')

  response = ssm.get_parameter(
    Name=f'/{product_name}/SLACK_WEBHOOK_URL',
    WithDecryption=True
  )
  return response['Parameter']['Value']

def post_slack(message, product_name):
  send_data = {
    "text": message,
  }
  send_text = json.dumps(send_data)
  request = urllib.request.Request(
    slack_webhook_url(product_name),
    data=send_text.encode('utf-8'),
    method="POST"
  )
  with urllib.request.urlopen(request) as response:
    response.read().decode('utf-8')

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
  message = '\n'.join(event['message'] for event in json_data['logEvents'])

  # SNS件名設定
  log_group = json_data['logGroup']
  log_stream = json_data['logStream']
  if 'tasuki-land' in log_group:
    product_name = 'TASUKI_LAND'
  else:
    product_name = 'TASUKI_FUNDS'
  #ロググループ名、ログストリーム名をsubjectに設定
  subject = log_group + ' ' + log_stream
  cw_url = f'https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#logsV2:log-groups/log-group/{log_group.replace("/", "$252F")}/log-events/{log_stream.replace("/", "$252F")}'

  ng_words = ['PumaWorkerKiller', 'ActionController::RoutingError', 'Can\'t verify CSRF token authenticity.', 'ActionView::MissingTemplate']
  # すべてのNGワードを含まない場合
  if sum([m not in message for m in ng_words]) == len(ng_words):
    sns_client.publish(
      TopicArn = sns_topic_arn,
      Subject = subject,
      Message = message
    )

    post_slack(f'<{cw_url}|{subject}>\n{message}', product_name)
