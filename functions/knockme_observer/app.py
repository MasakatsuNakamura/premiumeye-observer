from __future__ import print_function
import json
import boto3
from botocore.exceptions import ClientError
import datetime
import os
import re

print('Loading function')

def lambda_handler(event, context):
  """
  Knockmeの監視用スクリプト
  """
  #print("Received event: " + json.dumps(event, indent=2))
  channel = event['Records'][0]['Sns']['TopicArn']
  match = re.search('(Production|Stage|Stage2)$', channel)
  channel = f'notification_{match[0].lower()}' if match else 'awschat'

  message_orig = event['Records'][0]['Sns']['Message']
  message = json.loads(message_orig)

  logs = boto3.client('logs')
  sns = boto3.client('sns')

  # SNS message からメトリックネームとネームスペースを取得
  metricfilters = logs.describe_metric_filters(
    metricName = message['Trigger']['MetricName'] ,
    metricNamespace = message['Trigger']['Namespace']
  )

  # CloudWatch Alarm のピリオドの2倍 + 10秒
  intPeriod = message['Trigger']['Period'] * 2 + 10

  # CloudWatch Logsを検索するために必要な項目のセット
  # unixtime へ変換している
  strEndTime = datetime.datetime.strptime(message['StateChangeTime'], '%Y-%m-%dT%H:%M:%S.%f%z')
  strStartTime = strEndTime - datetime.timedelta(seconds = intPeriod)
  alarmEndTime = int(strEndTime.timestamp()) * 1000
  alarmStartTime = int(strStartTime.timestamp()) * 1000

  # CloudWatch Logsを検索して該当のログメッセージを取得する
  params = {
    'logGroupName': metricfilters['metricFilters'][0]['logGroupName'],
    'startTime': alarmStartTime,
    'endTime': alarmEndTime,
    'filterPattern': metricfilters['metricFilters'][0]['filterPattern']
  }
  events = []
  while True:
    response = logs.filter_log_events(**params)
    events += response['events']
    if 'nextToken' in response:
      params['nextToken'] = response['nextToken']
    else:
      break

  #SNSのタイトル、本文整形
  alarm_name = message['AlarmName']
  events.sort(key=lambda x: x['timestamp'])
  message = '\n'.join(e['message'] for e in events)

  #SNS Publish(メール送信)
  if os.environ['EMAIL_SNS_TOPIC_ARN'] != '' and channel == 'notification_production':
    sns.publish(
      TopicArn = os.environ['EMAIL_SNS_TOPIC_ARN'],
      Message = message,
      Subject = alarm_name
    )

  #SNS Publish(Slack通知)
  sns.publish(
    TopicArn = os.environ['SLACK_SNS_TOPIC_ARN'],
    Message = alarm_name + '\n' + message,
    Subject = channel,
  )
