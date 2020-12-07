import boto3
import datetime
import re

ssm = boto3.client('ssm')
ecs = boto3.client('ecs', 'ap-northeast-1')

def instance_avairable(activation_id):
  instances = []
  params = {
    'Filters': [
      {
        'Key': 'PingStatus',
        'Values': [ 'Online' ]
      },
      {
        'Key': 'ActivationIds',
        'Values': [ activation_id ]
      }
    ]
  }
  while True:
    res = ssm.describe_instance_information(**params)
    instances += res['InstanceInformationList']
    if 'NextToken' in res:
      params['NextToken'] = res['NextToken']
    else:
      break
  return(len(instances) > 0)

def activations():
  acts = []
  params = {}
  while True:
    res = ssm.describe_activations(**params)
    acts += res['ActivationList']
    if 'NextToken' in res:
      params['NextToken'] = res['NextToken']
    else:
      break
  return(acts)

def lambda_handler(event, context):
  try:
    for act in activations():
      expire_date = act['ExpirationDate'].astimezone(datetime.timezone.utc)
      match = re.search(r'^(prod|stg|stg\d+)-knockme-activation-.*$', act['Description'])
      # 対象のアクティベーションが24時間以内に失効する場合、更新する。
      if match and expire_date < datetime.datetime.now().astimezone(datetime.timezone.utc) + datetime.timedelta(hours = 24):
        print(act)
        # 当該アクティベーションに紐づくインスタンスがない場合、アクティベーションを削除する
        if not instance_avairable(act['ActivationId']):
          ssm.delete_activation(ActivationId=act['ActivationId'])

        activation_name = match[0]
        stage = match[1]

        res = ssm.create_activation(
          Description=activation_name,
          IamRole='service-role/AmazonEC2RunCommandRoleForManagedInstances',
          RegistrationLimit=1000,
          ExpirationDate=datetime.datetime.now() + datetime.timedelta(days = 29)
        )
        ssm.put_parameter(
          Name=f'{stage.upper()}_SSM_AGENT_ID',
          Value=res['ActivationId'],
          Type='SecureString',
          KeyId='alias/aws/ssm',
          Overwrite=True,
          DataType='text'
        )
        ssm.put_parameter(
          Name=f'{stage.upper()}_SSM_AGENT_CODE',
          Value=res['ActivationCode'],
          Type='SecureString',
          KeyId='alias/aws/ssm',
          Overwrite=True,
          DataType='text'
        )

  except Exception as e:
    print(e)
