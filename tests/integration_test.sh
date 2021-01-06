#!/bin/sh
docker-compose up -d
export LOCALSTACK_ENDPOINT=http://localstack:4566
export S3_BUCKET=direct-upload
docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 rm s3://$S3_BUCKET --recursive
docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 rb s3://$S3_BUCKET
docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 mb s3://$S3_BUCKET
cat << EOS | gzip -c | docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 cp - s3://$S3_BUCKET/process_logs/1/2020-12-22/120000/process_log.json.gz
{
  "recorded_at": "2020-11-30T12:00:00.000+09:00",
  "processes": ["aaaa","bbbb","cccc"]
}
EOS
cat << EOS1 | gzip -c | docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 cp - s3://$S3_BUCKET/process_logs/1/2020-12-22/130000/process_log.json.gz
{
  "recorded_at": "2020-11-30T13:00:00.000+09:00",
  "processes": ["aaaa","bbbb"]
}
EOS1
cat << EOS2 | gzip -c | docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 cp - s3://$S3_BUCKET/process_logs/1/2020-12-22/140000/process_log.json.gz
{
  "recorded_at": "2020-11-30T14:00:00.000+09:00",
  "processes": ["aaaa"]
}
EOS2
sam local invoke --env-vars local_env.json SummarizeProcessLogsFunction --docker-network knockme-observer_default -e events/s3_put_event.json
echo
docker-compose exec -T localstack aws --endpoint $LOCALSTACK_ENDPOINT s3 cp s3://$S3_BUCKET/process_logs/1/2020-12-22/summary.json.gz - | gzip -cd
