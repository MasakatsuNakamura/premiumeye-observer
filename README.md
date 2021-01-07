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

```sh
$ sam build
$ sam deploy  # Cloudformationスタックを確認後、yを押す必要があります
```

# プロジェクトのアンインストール方法

```sh
$ aws cloudformation delete-stack --stack-name knockme-observer
```

# ローカルでのLambdaの動作確認方法

```sh
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

## notify_instance_id

SSMエージェントが登録された際に、登録されたことをSlackで通知する関数

## update_activation

SSMのハイブリッドアクティベーションの有効期限が切れている場合、アクティベーションを自動で再作成する関数

## summarize_process_logs

Knockme!のプロセスログ収集用S3にプロセスログがPUTされたときに、非同期で集計を行う関数
