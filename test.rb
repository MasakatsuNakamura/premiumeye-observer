require 'aws-sdk-sns'

sns = Aws::SNS::Resource.new(region: 'ap-northeast-1')

topic = sns.topic('arn:aws:sns:ap-northeast-1:747245521221:KnockmeStageEmailTopic')

topic.publish({
  subject: 'Rubyからの送信テスト',
  message: "このメールはSNSで送っています"
})
