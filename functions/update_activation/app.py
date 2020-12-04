import boto3
import datetime
import re

ssm = boto3.client('ssm')
ecs = boto3.client('ecs', 'ap-northeast-1')

def lambda_handler(event, context):
  try:
    acts = ssm.describe_activations()['ActivationList']
    for act in acts:
      expire_date = datetime.datetime.fromisoformat(act['ExpirationDate'])
      # 24時間以内にアクティベーションの期限が切れる場合、更新する。
      if expire_date < datetime.datetime.now() + datetime.timedelta(hours = 24):
        ssm.delete_activation(ActivationId=act['ActivationId'])

        match = re.search(r'^(prod|stg|stg2)\-', act['Description'])
        stage = match[1]

        res = ssm.create_activation(
          Description=f'{stage}-knockme-activation-fargate-automated',
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
