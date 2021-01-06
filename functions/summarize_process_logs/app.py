from __future__ import print_function
import json
import boto3
from botocore.exceptions import ClientError
import datetime
import os
import re
import gzip

if 'LOCALSTACK_ENDPOINT' in os.environ:
  endpoint_url = { 'endpoint_url': os.environ['LOCALSTACK_ENDPOINT'] }
else:
  endpoint_url = {}

s3 = boto3.client('s3', 'ap-northeast-1', **endpoint_url)

def lambda_handler(event, context):
  """
  プロセスログを集計する
  """
  for record in event['Records']:
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    if m := re.search(r'^(?P<prefix>process_logs/\d+/\d{4}-\d{2}-\d{2}/)\d{6}/[^\.]+.json.gz$', key):
      params = { 'Bucket': bucket, 'Prefix': m['prefix'] }
      keys = []
      while True:
        res = s3.list_objects(**params)
        if 'Contents' not in res:
          break
        keys += [ obj['Key'] for obj in res['Contents'] ]
        if 'NextMarker' in res:
          params['Marker'] = res['NextMarker']
        else:
          break
      process_count = {}
      last_recorded_at = None
      logs_count = 0
      for key in keys:
        with gzip.open(s3.get_object(Bucket=bucket, Key=key)['Body'], 'rt') as f:
          process_log = json.loads(f.read())
        if 'recorded_at' not in process_log or 'processes' not in process_log:
          continue
        if last_recorded_at:
          if datetime.datetime.fromisoformat(last_recorded_at) < datetime.datetime.fromisoformat(process_log['recorded_at']):
            last_recorded_at = process_log['recorded_at']
        else:
          last_recorded_at = process_log['recorded_at']
        logs_count += 1
        for process in process_log['processes']:
          if process in process_count:
            process_count[process] += 1
          else:
            process_count[process] = 1
      summary = { 'process_rates': [], 'last_recorded_at': last_recorded_at }
      for process, count in process_count.items():
        summary['process_rates'].append({
          'process_name': process,
          'percentage': count * 100.0 / logs_count
        })
      summary['process_rates'].sort(key=lambda x: (-x['percentage'], x['process_name'].lower().encode('utf-8')))
      upload_file = gzip.compress(bytes(json.dumps(summary, ensure_ascii=False, indent=2), 'utf-8'))
      s3.put_object(Bucket=bucket, Key=m['prefix'] + "summary.json.gz", Body=upload_file)
  return "Done"