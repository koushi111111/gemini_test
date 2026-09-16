# tx_hackathon_gc

Flutter(フロント) + FastAPI(バックエンド) + Gemini on Google Cloud を組み合わせたアプリケーション。
**SPEC 駆動開発**(要件 → 設計 → タスク → 実装)で開発を進める。

> このリポジトリの「正」となるドキュメントは本 README です。構成・手順・方針を変更したら、**同じコミットで README も更新**してください(運用ルールは [CLAUDE.md](CLAUDE.md) 参照)。

---

## 1. 技術スタック

| 領域 | 採用技術 | 備考 |
| --- | --- | --- |
| フロントエンド | Flutter 3.41.x / Dart 3.11.x | Web / iOS / Android をターゲットに生成済み。開発は Web 中心 |
| バックエンド | Python 3.12 / FastAPI | `app/` 配下にレイヤ分割(api / services / schemas / core) |
| パッケージ管理 | uv | `backend/pyproject.toml` + `backend/uv.lock` で固定 |
| 外部 API | Gemini(Google Cloud Vertex AI) | `google-genai` SDK 経由。AI Studio の API キー方式にも切替可 |
| 実行環境 | Docker Compose | フロント / バックを 1 コマンドで同時起動 |
| 設定管理 | pydantic-settings / `.env` | 秘匿情報は Git 管理外 |

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────────────┐
│ ブラウザ / モバイル                                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Flutter App  (localhost:8080)                                 │  │
│  │                                                               │  │
│  │   features/<機能>/  ── 画面(Widget) + 状態                    │  │
│  │            │                                                  │  │
│  │            ▼                                                  │  │
│  │   features/<機能>/*_repository.dart  ── データアクセス        │  │
│  │            │                                                  │  │
│  │            ▼                                                  │  │
│  │   core/api_client.dart  ── HTTP / JSON / 例外変換             │  │
│  └───────────────────────────────┬───────────────────────────────┘  │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │ HTTP (JSON)  /api/v1/**
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FastAPI Backend  (localhost:8000)                                   │
│                                                                     │
│   app/main.py         ── アプリ生成 / CORS / lifespan               │
│            │                                                        │
│   app/api/router.py   ── ルータ集約                                 │
│            │                                                        │
│   app/api/routes/     ── エンドポイント(入出力の検証と HTTP 変換)   │
│            │                                                        │
│   app/services/       ── ビジネスロジック / 外部 API 呼び出し       │
│            │              例外は業務例外(GeminiError 等)に変換      │
│   app/schemas/        ── Pydantic モデル(API 契約)                  │
│   app/core/           ── 設定(config) / ロギング                    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ google-genai SDK (ADC 認証)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Google Cloud                                                        │
│   Vertex AI ── Gemini (gemini-2.5-flash)                            │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 レイヤの責務(この境界を守る)

| レイヤ | 責務 | やってはいけないこと |
| --- | --- | --- |
| `app/api/routes/` | リクエスト検証、HTTP ステータスへの変換、DI | ビジネスロジック、SDK の直接呼び出し |
| `app/services/` | ユースケース実装、外部 API 呼び出し、例外の正規化 | `HTTPException` を投げる、FastAPI に依存する |
| `app/schemas/` | API の入出力契約(Pydantic) | 永続化や外部 API のモデルを兼ねる |
| `app/core/` | 設定・ロギングなど横断関心事 | 機能固有のロジック |
| `lib/features/*/` | 画面と状態、機能ごとの Repository | 他 feature の内部への直接依存 |
| `lib/core/` | HTTP クライアント、共通設定 | 画面固有の処理 |

### 2.3 リクエストの流れ(チャット機能の例)

```
ユーザー入力
  → ChatScreen._send()
  → ChatRepository.sendMessage()
  → POST /api/v1/chat                     (ApiClient)
  → chat.py: ChatRequest で検証            (routes)
  → GeminiService.generate_reply()         (services)
  → client.aio.models.generate_content()  → Vertex AI / Gemini
  → ChatResponse(reply, model)
  → 画面に吹き出しとして描画
```

失敗時は `GeminiError` → HTTP 502 → `ApiException` → 画面上のバナー、という順に変換される。

### 2.4 ディレクトリ構成

```
tx_hackathon_gc/
├── README.md                 # 本ドキュメント(構成・手順の正)
├── CLAUDE.md                 # Claude Code 向けの作業ルール
├── docker-compose.yml        # フロント + バックの同時起動
├── backend/                  # FastAPI + uv
│   ├── pyproject.toml / uv.lock
│   ├── .env.example          # 環境変数の雛形(.env は Git 管理外)
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py           # エントリポイント(create_app)
│   │   ├── api/
│   │   │   ├── router.py     # ルータ集約
│   │   │   └── routes/       # health.py, chat.py, ...
│   │   ├── core/             # config.py, logging.py
│   │   ├── schemas/          # Pydantic モデル
│   │   └── services/         # gemini.py, ...
│   └── tests/                # pytest
├── frontend/                 # Flutter
│   ├── pubspec.yaml
│   ├── Dockerfile            # dev(ホットリロード) / prod(nginx) の 2 ステージ
│   ├── lib/
│   │   ├── main.dart
│   │   ├── core/             # app_config.dart, api_client.dart
│   │   └── features/         # 機能ごと(chat/ など)
│   └── test/
├── docs/
│   └── spec/                 # SPEC 駆動開発のドキュメント
│       ├── README.md         # 運用ルール
│       ├── _template/        # requirements / design / tasks の雛形
│       └── 000-local-dev-environment/
└── infra/
    └── secrets/              # GCP サービスアカウントキー等(Git 管理外)
```

---

## 3. セットアップ

### 3.1 前提ツール

| ツール | 確認コマンド | 補足 |
| --- | --- | --- |
| Flutter 3.41+ | `flutter --version` | Web 開発なら Chrome も必要 |
| uv | `uv --version` | Python 3.12 は uv が自動取得する |
| Docker Desktop | `docker compose version` | Compose v2 |
| gcloud CLI | `gcloud --version` | ADC 認証を使う場合 |

### 3.2 環境変数

```bash
cp backend/.env.example backend/.env
```

`backend/.env` の主な項目:

| 変数 | 既定値 | 説明 |
| --- | --- | --- |
| `ENVIRONMENT` | `local` | `local` / `dev` / `prod`。`local` 以外は JSON ログになる |
| `GOOGLE_GENAI_USE_VERTEXAI` | `true` | `true`=Vertex AI 経由 / `false`=AI Studio の API キー |
| `GOOGLE_CLOUD_PROJECT` | (必須) | GCP プロジェクト ID |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Vertex AI のリージョン |
| `GOOGLE_API_KEY` | 空 | `GOOGLE_GENAI_USE_VERTEXAI=false` のときのみ使用 |
| `GEMINI_MODEL` | `gemini-2.5-flash` | 使用モデル |
| `GEMINI_TEMPERATURE` / `GEMINI_MAX_OUTPUT_TOKENS` | `0.7` / `2048` | 生成パラメータ |

### 3.3 Google Cloud 認証

ローカルでネイティブ起動する場合は **ADC(推奨)**:

```bash
gcloud auth application-default login
gcloud config set project <PROJECT_ID>
gcloud services enable aiplatform.googleapis.com
```

Docker で動かす場合は **サービスアカウントキー**を使う(compose が `/secrets` にマウントする):

```
infra/secrets/gcp-sa.json   ← Vertex AI User ロールを付与した SA のキー(Git 管理外)
```

---

## 4. 起動方法

### 4.1 Docker Compose(フロント + バックを同時起動)

```bash
docker compose up --build
```

| URL | 内容 |
| --- | --- |
| http://localhost:8080 | Flutter Web アプリ |
| http://localhost:8000/docs | FastAPI の Swagger UI |
| http://localhost:8000/api/v1/health | ヘルスチェック |

停止は `docker compose down`(ボリュームも消す場合は `-v`)。

### 4.2 ネイティブ起動(開発中はこちらが高速)

バックエンド:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

フロントエンド:

```bash
cd frontend
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

---

## 5. テスト / 静的解析

```bash
# バックエンド
cd backend
uv run python -m pytest          # テスト
uv run ruff check .              # Lint
uv run ruff format .             # フォーマット
uv run python -m mypy app        # 型チェック(下記の注意参照)

# フロントエンド
cd frontend
flutter analyze
flutter test
```

> **Windows のアプリケーション制御ポリシーについて**
> - `uv run pytest`(`pytest.exe`)はブロックされることがあるため、`uv run python -m pytest` を使う。
> - mypy はネイティブ拡張(`*_mypyc.pyd`)がブロックされ、現状この開発マシンでは実行できない。
>   型チェックは Docker(`docker compose run --rm backend python -m mypy app`)または CI で実行する。

---

## 6. SPEC 駆動開発の進め方

機能ごとに `docs/spec/<連番>-<機能名>/` を作り、**要件 → 設計 → タスク → 実装** の順で進める。
詳細は [docs/spec/README.md](docs/spec/README.md)、雛形は [docs/spec/_template/](docs/spec/_template/)。

```
docs/spec/001-user-authentication/
├── requirements.md   # なぜ / 誰が何をできるか / 受け入れ基準(AC)
├── design.md         # どう作るか(API・データモデル・画面・エラー・テスト方針)
└── tasks.md          # 30〜90 分粒度の作業分解(チェックボックス)
```

原則:

1. **requirements.md が承認されるまで design.md を書かない。design.md が承認されるまで実装しない。**
2. 受け入れ基準(AC)はテスト可能な粒度で書き、`tasks.md` の各タスクから参照する。
3. 実装中に設計が変わったら、コードと同じコミットで `design.md` を更新する。
4. 機能完了時に本 README の機能一覧 / アーキテクチャを更新する。
5. ブランチ名は spec 名に揃える(例: `feat/001-user-authentication`)。

### 実装済み / 進行中の機能

| spec | 機能 | ステータス |
| --- | --- | --- |
| [000-local-dev-environment](docs/spec/000-local-dev-environment/) | ローカル開発環境の整備(疎通用チャット含む) | 実装完了 / `docker compose up` と Gemini 実応答の確認待ち |

---

## 7. 新しい機能を追加するときの手順

1. `docs/spec/_template/` をコピーして `docs/spec/<連番>-<機能名>/` を作る。
2. `requirements.md` → `design.md` → `tasks.md` を順に作成し、レビューを受ける。
3. バックエンド: `app/schemas/` にモデル → `app/services/` にロジック → `app/api/routes/` にエンドポイント → `app/api/router.py` に登録。
4. フロントエンド: `lib/features/<機能>/` にモデル / Repository / 画面を追加。
5. テストを追加し(`backend/tests/`, `frontend/test/`)、`pytest` と `flutter test` を通す。
6. `tasks.md` のチェックを埋め、README の機能一覧を更新する。

---

## 8. トラブルシューティング

| 症状 | 対処 |
| --- | --- |
| `GOOGLE_CLOUD_PROJECT が未設定です` | `backend/.env` にプロジェクト ID を設定する |
| 403 / PermissionDenied | `aiplatform.googleapis.com` の有効化と、SA への Vertex AI User ロール付与を確認 |
| フロントから API が呼べない(CORS) | `backend/app/core/config.py` の `cors_origins` に接続元 URL を追加 |
| コンテナでコード変更が反映されない | Windows では `WATCHFILES_FORCE_POLLING=true`(compose 設定済み)を確認 |
| `uv run pytest` がブロックされる | `uv run python -m pytest` を使う |
| `mypy` が `DLL load failed` で落ちる | ローカルのアプリ制御ポリシーによるもの。Docker または CI で型チェックする |
| Flutter コンテナのビルドが遅い | 開発中はネイティブ起動(4.2)を使い、compose は結合確認時に使う |
