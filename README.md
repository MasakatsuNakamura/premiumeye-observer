# tasuki-observer

AWS SAMを用いたTasukiTech監視用SAMリポジトリ

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
$ sam build
$ sam deploy
```

# プロジェクトのアンインストール方法

```sh
$ aws cloudformation delete-stack --stack-name tasuki-observer
```

# ローカルでのLambdaの動作確認方法

```sh
$ sam build
$ sam local invoke 関数名 -e イベント.json
```
