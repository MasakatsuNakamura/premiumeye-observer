# knockme_observer

AWS SAMを用いたKnockme監視用SAMリポジトリ

# 使い方

## AWS SAMをインストールする(Macの場合)

SAMのインストールには、Mac以外の場合でも`homebrew`を用いるのが一番手軽です。

### 前提

- `python3`
- `aws-cli` (`aws configure`が済んでいること)
- `docker`
- `homebrew`

### インストール手順

```sh
$ brew tap aws/tap
$ brew install aws-sam-cli
```

# プロジェクトのデプロイ方法

`--stack-name`の打ち間違いに注意してください。入力をミスすると新しいCloudFormationスタックが作成されます。

```sh
$ sam build   # 共通
# 本番デプロイ
$ sam deploy --parameter-overrides Environment=production --stack-name knockme-observer  # Cloudformationスタックを確認後、yを押す必要があります
# ステージングデプロイ
$ sam deploy --parameter-overrides Environment=stage --stack-name knockme-observer-stage  # Cloudformationスタックを確認後、yを押す必要があります
# ステージング2デプロイ
$ sam deploy --parameter-overrides Environment=stage2 --stack-name knockme-observer-stage2  # Cloudformationスタックを確認後、yを押す必要があります
```

# プロジェクトのアンインストール方法

```sh
# 本番
$ aws cloudformation delete-stack --stack-name knockme-observer
# ステージング
$ aws cloudformation delete-stack --stack-name knockme-observer-stage
# ステージング2
$ aws cloudformation delete-stack --stack-name knockme-observer-sgate2
```

# ローカルでのLambdaの動作確認方法

```sh
$ sam build
$ sam local invoke 関数名 -e イベント.json
```

# プロジェクトのテスト方法

(テストが実装されているのはsummarize_process_logs関数のみです)

```sh
$ sh tests/integration_test.sh
```

# 含まれる関数とその機能

## knockme_observer

CLoudWatch AlarmのトリガをもとにCloudWatch Logsの関連ログを取得し、SNSで発信する関数

## summarize_process_logs

Knockme!のプロセスログ収集用S3にプロセスログがPUTされたときに、非同期で集計を行う関数
