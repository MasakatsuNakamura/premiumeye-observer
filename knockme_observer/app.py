from __future__ import print_function
import json
import boto3
from botocore.exceptions import ClientError
import datetime
import os

print('Loading function')

def lambda_handler(event, context):
  """
  Knockmeの監視用スクリプト
  """
  #print("Received event: " + json.dumps(event, indent=2))
  message_orig = event['Records'][0]['Sns']['Message']
  message = json.loads(message_orig)

  try:
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
    response = logs.filter_log_events(
      logGroupName = metricfilters['metricFilters'][0]['logGroupName'],
      startTime = alarmStartTime,
      endTime = alarmEndTime,
      filterPattern = metricfilters['metricFilters'][0]['filterPattern'],
    )
    events = response['events']
    while 'nextToken' in response:
      response = logs.filter_log_events(
        logGroupName = metricfilters['metricFilters'][0]['logGroupName'],
        startTime = alarmStartTime,
        endTime = alarmEndTime,
        filterPattern = metricfilters['metricFilters'][0]['filterPattern'],
        nextToken = response['nextToken']
      )
      events += response['events']

    #SNSのタイトル、本文整形
    alarm_name = message['AlarmName']
    new_state = message['NewStateValue']
    events = sorted(events, key=lambda x: x['timestamp'])
    message = f'state is now {new_state}:\n\n' + '\n'.join(e['message'] for e in events)

    #SNS Publish(メール送信)
    sns.publish(
      TopicArn = os.environ['SNS_TOPIC_ARN'],
      Message = message,
      Subject = alarm_name
    )

    #SNS Publish(Slack通知)
    sns.publish(
      TopicArn = os.environ['SLACK_SNS_TOPIC_ARN'],
      Message = message,
      Subject = alarm_name,
    )

  except Exception as e:
    print(e)
