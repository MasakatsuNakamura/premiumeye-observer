import json
import gzip
import base64
import re
import boto3
import os

sns = boto3.client('sns', 'ap-northeast-1')

def lambda_handler(event, context):
  try:
    b64data = event['awslogs']['data']
    compressed_data = base64.b64decode(b64data)
    payload_str = gzip.decompress(compressed_data)
    print(payload_str)
    payload = json.loads(payload_str)

    if re.search(r'prod-', payload['logGroup']):
      channel = 'notification_production'
    elif re.search(r'stg-', payload['logGroup']):
      channel = 'notification_stage'
    elif re.search(r'stg2-', payload['logGroup']):
      channel = 'notification_stage2'

    for event in payload['logEvents']:
      match = re.search(r"Successfully registered the instance with AWS SSM using Managed instance-id: ([0-9a-z\-]+)$", event['message'])
      if match:
        sns.publish(
          TopicArn = os.environ['SLACK_SNS_TOPIC_ARN'],
          Message = "SSMエージェント更新成功\n" + f"{payload['logGroup']} にSSMエージェントが登録されました。インスタンスIDは {match[1]} です。",
          Subject = channel,
        )
    return True
  except Exception as e:
    print(e)
    return False
