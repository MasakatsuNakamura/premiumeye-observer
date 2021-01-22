from __future__ import print_function
import json
import boto3
from botocore.exceptions import ClientError
import datetime
import os
import re
import gzip
import traceback

if 'LOCALSTACK_ENDPOINT' in os.environ and os.environ['LOCALSTACK_ENDPOINT'] != '':
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
    print(f'receive event put s3://{bucket}/{key}')
    if m := re.search(r'^process_logs/(?P<id_date>\d+/\d{4}-\d{2}-\d{2})/\d{6}/[^\.]+.json.gz$', key):
      params = { 'Bucket': bucket, 'Prefix': 'process_logs/' + m['id_date'] + '/' }
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
      keys = [key for key in keys if key.endswith('.json.gz')]
      process_count = {}
      last_recorded_at = None
      logs_count = 0
      for key in keys:
        print(f'processing s3://{bucket}/{key} ...')
        try:
          with gzip.open(s3.get_object(Bucket=bucket, Key=key)['Body'], 'rt') as f:
            process_log = json.loads(f.read())
          if 'recorded_at' not in process_log or 'processes' not in process_log:
            continue
          if last_recorded_at:
            if datetime.datetime.fromisoformat(last_recorded_at) < datetime.datetime.fromisoformat(process_log['recorded_at']):
              last_recorded_at = process_log['recorded_at']
          else:
            last_recorded_at = process_log['recorded_at']
          logs_count += len(process_log['processes'])
          for process in process_log['processes']:
            if process in process_count:
              process_count[process] += 1
            else:
              process_count[process] = 1
        except:
          traceback.print_exc()
      summary = { 'process_rates': [], 'last_recorded_at': last_recorded_at }
      if len(process_count) > 0:
        for process, count in process_count.items():
          summary['process_rates'].append({
            'process_name': process,
            'percentage': count * 100.0 / logs_count
          })
        summary['process_rates'].sort(key=lambda x: (-x['percentage'], x['process_name'].lower().encode('utf-8')))
        upload_file = gzip.compress(bytes(json.dumps(summary, ensure_ascii=False, indent=2), 'utf-8'))
        s3.put_object(Bucket=bucket, Key='process_logs_summary/' + m["id_date"] + '.json.gz', Body=upload_file)
        return "Done"
      else
        return "No Summary"
