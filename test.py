from __future__ import print_function
import json
import boto3
from botocore.exceptions import ClientError
import datetime
import os

logs = boto3.client('logs')

strEndTime = datetime.datetime.now()
strStartTime = strEndTime - datetime.timedelta(minutes = 60)
#print(f"{strStartTime} {strEndTime}")
alarmEndTime = int(strEndTime.timestamp()) * 1000
alarmStartTime = int(strStartTime.timestamp()) * 1000

logGroupName = '/ecs/stg-web-task-fargate'
#logGroupName = '/ecs/prod-web-task-fargate-1_0_0'
#filterPattern = 'ERROR WebSocket error occurred NilClass'
filterPattern = 'ERROR'

# CloudWatch Logsを検索して該当のログメッセージを取得する
response = logs.filter_log_events(
    logGroupName = logGroupName,
    startTime = alarmStartTime,
    endTime = alarmEndTime,
    filterPattern = filterPattern,
)
events = response['events']
while 'nextToken' in response:
    response = logs.filter_log_events(
        logGroupName = logGroupName,
        startTime = alarmStartTime,
        endTime = alarmEndTime,
        filterPattern = filterPattern,
        nextToken = response['nextToken']
    )
    events += response['events']

events = sorted(events, key=lambda x: x['timestamp'])
count = {}
for e in events:
    if e['logStreamName'] in count:
        if e['message'] not in count[e['logStreamName']]:
            count[e['logStreamName']].append(e['message'])
    else:
        count[e['logStreamName']] = [e['message']]

print(json.dumps(count, indent=2))
