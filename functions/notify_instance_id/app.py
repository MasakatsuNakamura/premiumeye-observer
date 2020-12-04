import json
import gzip
import base64
import boto3
import os

def lambda_handler(event, context):
  try:
    b64data = event['awslogs']['data']
    compressed_data = base64.b64decode(b64data)
    payload_str = gzip.decompress(compressed_data)
    # 解凍したペイロードをログに記録
    print(payload_str)
    payload = json.loads(payload_str)

    channel = ''
    log_group = payload['logGroup']
    if log_group.startswith('prod-'):
      channel = 'notification_production'
    elif log_group.startswith('stg-'):
      channel = 'notification_stage'
    elif log_group.startswith('stg2-'):
      channel = 'notification_stage2'

    if channel != '':
      sns = boto3.client('sns', 'ap-northeast-1')
      for event in payload['logEvents']:
        if "Successfully registered the instance with AWS SSM" in event['message']:
          instance_id = event['message'].split(' ')[-1]
          sns.publish(
            TopicArn = os.environ['SLACK_SNS_TOPIC_ARN'],
            Message = "SSMエージェント更新成功\n" + f"{log_group} にSSMエージェントが登録されました。インスタンスIDは {instance_id} です。",
            Subject = channel
          )
    return True
  except Exception as e:
    print(e)
    return False
