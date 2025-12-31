# Slack AI Bot

LangGraphベースのマルチエージェント型Slack AI Botです。ユーザーの質問に対してWeb検索とLLMの知識を組み合わせて回答を生成します。

## ドキュメント

各種設計図は`docs/`フォルダに格納されています：

- **[データベーススキーマ](docs/database_schema.drawio)**: PostgreSQL テーブル設計
- **[GCPインフラ構成図](docs/gcp_infrastructure.drawio)**: Cloud Run、Cloud SQL、VPC等の構成
- **[エージェントワークフロー図](docs/agent_workflow_ja.drawio)**: マルチエージェントの処理フロー

## 主な機能

### マルチエージェントワークフロー
- **Supervisorエージェント**: タスク計画の作成と最終回答の統合
- **Web検索エージェント**: Google Custom Searchを使った情報収集と結果評価（最大2回の再試行）
- **一般回答エージェント**: Google Gemini APIを活用したLLM知識ベースからの直

### Slack連携
- **Socket Mode**: ローカル開発用（外部公開不要）
- **HTTP Mode**: 本番環境用（FastAPIベース）
- スレッド対応、リアクションによるフィードバック機能

## プロジェクト構造

```
.
├── src/
│   ├── application/              # アプリケーション層（ユースケース、DTO）
│   ├── domain/                   # ドメイン層（モデル、リポジトリ、サービス）
│   ├── infrastructure/           # インフラ層（DB、外部API、LangGraphエージェント）
│   ├── presentation/             # プレゼンテーション層（Slackコントローラー）
│   ├── config/                   # 設定
│   ├── log/                      # ロガー
│   ├── di_container.py           # DIコンテナ
│   └── main.py                   # エントリーポイント
├── tests/                        # テストコード
├── migrations/                   # DBマイグレーション
├── docs/                         # 設計図（drawio）
├── terraform/                    # Infrastructure as Code
├── .github/workflows/            # CI/CD
├── compose.yml
├── Dockerfile
└── pyproject.toml
```

## 技術スタック

- **言語**: Python 3.12
- **フレームワーク**: LangGraph, FastAPI, Slack Bolt
- **データベース**: PostgreSQL
- **インフラ**: Google Cloud (Cloud Run, Cloud SQL, Artifact Registry, Secret Manager)
- **外部API**: Google Gemini API, Google Custom Search API
- **開発ツール**: uv, Docker, Terraform, GitHub Actions, pytest

## 環境構築

### ローカル開発環境

#### 前提条件
- Docker & Docker Composeがインストールされていること
- Slack Appが作成されていること（Socket Mode有効化）
- Google Cloud ProjectでGemini APIとCustom Search APIが有効化されていること
  - **Gemini API**: Google Cloud Consoleで「Generative Language API」を有効化し、APIキーを作成
  - **Custom Search API**:
    1. [Programmable Search Engine](https://programmablesearchengine.google.com/)にアクセス
    2. 「新しい検索エンジンを追加」をクリック
    3. 検索対象を「ウェブ全体を検索」に設定
    4. 作成後、検索エンジンIDをコピー（これが`GOOGLE_CSE_ID`）
    5. Google Cloud Consoleで「Custom Search API」を有効化し、同じAPIキーを使用

#### 1. 環境変数の設定

```bash
cp .env.sample .env
```

`.env`を編集して以下を設定：

```bash
# Slack Settings (Socket Mode)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here  # Socket Mode用
SLACK_SIGNING_SECRET=your-signing-secret-here

# Google API
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CSE_ID=your-custom-search-engine-id-here

# Database (Docker Compose)
POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/slackaibot

# Environment
ENV=local
```

**Slack App設定（Socket Mode）**:
1. Slack App設定ページで「Socket Mode」を有効化
2. App-Level Tokenを生成（scope: `connections:write`）
3. Bot Token Scopesを追加: `app_mentions:read`, `channels:history`, `chat:write`, `groups:history`, `im:history`, `mpim:history`, `reactions:read`, `reactions:write`
4. Event Subscriptionsを追加: `app_mention`, `message.groups`, `message.im`
5. 「App Home」タブで「Messages Tab」を有効化（DMでやり取りするため）

#### 2. アプリケーションの起動

```bash
docker compose up --build
```

#### 3. 動作確認

以下のいずれかの方法でボットと対話：
- **チャンネル**: ボットをチャンネルに招待し、`@BotName こんにちは`とメンション
- **DM**: ボットとのDMで直接メッセージを送信

#### テストの実行

```bash
docker compose exec app uv run pytest
```

---

### 本番環境（GCP）

#### 前提条件
- Google Cloud CLIがインストールされていること
- GCPプロジェクトが作成されていること
- 必要なAPIが有効化されていること:
  - Cloud Run API
  - Cloud SQL Admin API
  - Artifact Registry API
  - Secret Manager API
  - Compute Engine API
- サービスアカウントが作成されていること

#### 1. Terraformで基盤リソースを作成

まず、Cloud RunとCloud SQL以外のリソースを作成します。

```bash
cd terraform/environment/dev
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`を編集：

```hcl
project_id             = "your-project-id"
region                 = "asia-northeast1"
environment            = "dev"
service_name           = "slackaibot"
service_account_email  = "your-service-account@developer.gserviceaccount.com"
```

`main.tf`でCloud RunとCloud SQLモジュールをコメントアウト：

```hcl
# module "cloudrun" {
#   ...
# }

# module "postgres" {
#   ...
# }
```

基盤リソースを作成：

```bash
terraform init
terraform plan
terraform apply
```

これで以下が作成されます：
- VPC Network & Subnet
- Artifact Registry
- Secret Manager（シークレットの箱のみ）

#### 2. Secret Managerに値を設定

GCPコンソールまたはgcloudコマンドでシークレット値を設定：

```bash
# Slack設定
echo -n "xoxb-your-bot-token" | gcloud secrets versions add dev-slack-bot-token --data-file=-
echo -n "your-signing-secret" | gcloud secrets versions add dev-slack-signing-secret --data-file=-

# Google API
echo -n "your-google-api-key" | gcloud secrets versions add dev-google-api-key --data-file=-
echo -n "your-custom-search-engine-id" | gcloud secrets versions add dev-google-cx-id --data-file=-

# PostgreSQL認証情報
echo -n "dbuser" | gcloud secrets versions add dev-postgres-user --data-file=-
echo -n "your-strong-password" | gcloud secrets versions add dev-postgres-password --data-file=-
```

#### 3. Cloud SQLとCloud Runを作成

`main.tf`のコメントアウトを解除：

```hcl
module "cloudrun" {
  ...
}

module "postgres" {
  ...
}
```

再度apply：

```bash
terraform plan
terraform apply
```

#### 4. Dockerイメージをビルド＆プッシュ

```bash
cd ../../..  # プロジェクトルートに戻る

# ビルド
docker build -t asia-northeast1-docker.pkg.dev/your-project-id/slackaibot-dev/slackaibot:latest .

# 認証
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# プッシュ
docker push asia-northeast1-docker.pkg.dev/your-project-id/slackaibot-dev/slackaibot:latest
```

#### 5. Cloud Runを再デプロイ

```bash
cd terraform/environment/dev
terraform apply
```

#### 6. Slack App設定（HTTP Mode）

1. Slack App設定ページで「Socket Mode」を無効化
2. 「Event Subscriptions」を有効化
3. Request URLにCloud RunのURL + `/slack/events`を設定（例: `https://your-service-xxx.run.app/slack/events`）

#### 7. GitHub ActionsでCI/CD（オプション）

`.github/workflows/deploy.yml`で自動デプロイを設定済み：
- `main`ブランチ → 本番環境
- `dev`ブランチ → 開発環境

リポジトリのSecretsに以下を設定：
- `GCP_PROJECT_ID`
- `GCP_SA_KEY` (サービスアカウントのJSONキー)
- `GCP_REGION`
