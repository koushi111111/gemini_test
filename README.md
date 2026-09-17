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
│   Vertex AI ── Gemini (gemini-3.8-flash)                            │
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
├── .github/
│   └── workflows/ci.yml      # push / PR 時の Lint・型チェック・テスト
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

### 5.1 ローカル

```bash
# バックエンド
cd backend
uv run python -m pytest          # テスト
uv run ruff check .              # Lint
uv run ruff format .             # フォーマット
uv run python -m mypy app        # 型チェック(下記の注意参照)

# フロントエンド
cd frontend
dart format .                    # フォーマット
flutter analyze                  # 静的解析
flutter test                     # テスト
```

> **Windows のアプリケーション制御ポリシーについて**
> - `uv run pytest`(`pytest.exe`)はブロックされることがあるため、`uv run python -m pytest` を使う。
> - mypy はネイティブ拡張(`*_mypyc.pyd`)がブロックされ、現状この開発マシンでは実行できない。
>   型チェックは Docker(`docker compose run --rm backend python -m mypy app`)または CI(5.2)で実行する。

### 5.2 CI(GitHub Actions)

`main` への push と `main` 向けの PR で [.github/workflows/ci.yml](.github/workflows/ci.yml) が自動実行される
(手動実行は Actions タブの "Run workflow")。3 ジョブが並列に走る。

| ジョブ | 実行内容 |
| --- | --- |
| `backend` | `uv sync --frozen` → `ruff check` → `ruff format --check` → **`mypy app`** → `pytest` |
| `frontend` | `flutter pub get` → `dart format --set-exit-if-changed` → `flutter analyze` → `flutter test` |
| `docker` | `docker compose config` の検証 → バックエンドイメージのビルド |

- ローカルで mypy が動かない環境でも、**型チェックは push 後に CI が必ず実行する**。
- 依存は `uv.lock` / `pubspec.lock` に固定され、CI はキャッシュを使って再現性のある環境で検証する。
- 外部 API(Gemini)は呼ばない。テストは全てスタブで完結させること。
- **ステータスチェック名 = ジョブの `name:`**。ルールセット(5.3)で指定するため、
  `backend` / `frontend` / `docker` の 3 つは安易に変更しない。変更する場合はルールセット側も直す。

### 5.3 CI を必須にする(ブランチ保護)

CI は作っただけでは「落ちてもマージできる」状態。`main` を保護して初めてゲートになる。

**前提**: 一度 push して CI を実行しておく。ステータスチェックは
**過去に実行された履歴からしか選択できない**ため、未実行だと候補に出てこない。

**手順**: リポジトリの **Settings → Rules → Rulesets → New ruleset → New branch ruleset**

| 設定項目 | 値 |
| --- | --- |
| Ruleset Name | `protect-main` |
| Enforcement status | `Active`(まず様子を見るなら `Evaluate` でドライラン) |
| Target branches | Add target → **Include default branch**(= `main`) |
| Restrict deletions | ON |
| Block force pushes | ON |
| Require a pull request before merging | ON(Required approvals は 1 人開発なら `0`) |
| Require status checks to pass | ON → Add checks で `backend` / `frontend` / `docker` を追加(Source: GitHub Actions) |
| Require branches to be up to date before merging | 任意(ON にすると main 更新のたびに再実行が必要) |

注意点:

- **private リポジトリでのブランチ保護 / ルールセットは有料プラン(Pro / Team 以上)が必要**。
  Free の private では設定できないため、public にするかプランを確認する。
- 必須にしたチェックが「一度も実行されない」状況(例: ワークフローに `paths` フィルタを足す)を作ると、
  PR が永久に pending になりマージできなくなる。必須チェックと実行条件は必ず揃える。
- 管理者も含めて例外なく適用される。緊急時は Bypass list に自分を追加するか、ルールセットを一時 `Disabled` にする。

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

作業中の Git 操作は §8 のコマンド一覧を参照。

---

## 8. Git コマンド一覧(初心者向け)

### 8.1 まず知っておく 4 つの場所

```
①作業ツリー          ②ステージ            ③ローカルリポジトリ    ④リモート(GitHub)
 手元のファイル  ──→  コミット予定の箱  ──→  手元の履歴       ──→  みんなの履歴
                git add            git commit          git push

                         ←────────────────────────────────  git pull
```

「保存した = Git に記録された」ではない。`add`(②へ) → `commit`(③へ) → `push`(④へ)の 3 段階を通す。

### 8.2 初回だけやること

```bash
# 名前とメールアドレス(コミットに記録される)
git config --global user.name "あなたの名前"
git config --global user.email "you@example.com"

# 既定ブランチ名を main にする / pull は rebase にして履歴を綺麗に保つ
git config --global init.defaultBranch main
git config --global pull.rebase true

# GitHub リポジトリを作って紐づける(gh CLI がある場合)
gh auth login
gh repo create tx_hackathon_gc --private --source=. --remote=origin

# gh を使わない場合(GitHub の Web 画面で空リポジトリを作ってから)
git remote add origin https://github.com/<ユーザー名>/tx_hackathon_gc.git

# 最初のコミットと push
git add .
git commit -m "chore: 開発環境の初期構築"
git push -u origin main
```

### 8.3 機能開発の 1 サイクル(この流れを繰り返す)

```bash
# 1. 最新の main から作業ブランチを作る(ブランチ名は spec に合わせる)
git switch main
git pull
git switch -c feat/001-user-authentication

# 2. コードを編集する …

# 3. 何を変えたか確認する
git status          # 変更されたファイルの一覧
git diff            # 変更内容そのもの

# 4. コミットする
git add .                                   # 全部を対象にする
git add backend/app/api/routes/auth.py      # ファイルを選ぶ場合
git commit -m "feat: ログイン API を追加"

# 5. GitHub に送る(初回は -u、2 回目以降は git push だけでよい)
git push -u origin feat/001-user-authentication

# 6. PR を作る → CI(backend / frontend / docker)が緑になったらマージ
gh pr create --fill
gh pr checks            # CI の状況を確認
gh pr merge --squash    # Web 画面のマージボタンでもよい

# 7. 後片付け
git switch main
git pull
git branch -d feat/001-user-authentication
```

### 8.4 よく使うコマンド

**確認する**

| コマンド | 何ができるか |
| --- | --- |
| `git status` | 今どのブランチにいて、何が変更 / ステージされているか |
| `git diff` | まだ `add` していない変更内容 |
| `git diff --staged` | `add` 済み(コミット予定)の変更内容 |
| `git log --oneline -10` | 直近 10 件のコミット履歴 |
| `git log --oneline --graph --all` | ブランチの分岐を図で表示 |
| `git show <コミットID>` | そのコミットの変更内容 |

**記録する / 送る**

| コマンド | 何ができるか |
| --- | --- |
| `git add <ファイル>` / `git add .` | コミット対象に加える |
| `git commit -m "メッセージ"` | 記録する |
| `git commit -am "メッセージ"` | 変更済みファイルを add + commit(新規ファイルは対象外) |
| `git push` | GitHub に送る |
| `git push -u origin <ブランチ名>` | 新しいブランチを初めて送るとき |
| `git pull` | GitHub の変更を取り込む |
| `git fetch` | 取り込まずに最新情報だけ取得する |

**ブランチ**

| コマンド | 何ができるか |
| --- | --- |
| `git branch` | ローカルのブランチ一覧 |
| `git switch <ブランチ名>` | ブランチを切り替える |
| `git switch -c <ブランチ名>` | 作って切り替える |
| `git switch -` | 直前にいたブランチに戻る |
| `git branch -d <ブランチ名>` | マージ済みブランチを削除 |
| `git merge main` | 作業ブランチに main の変更を取り込む |

**取り消す**(よく使う順)

| やりたいこと | コマンド | 補足 |
| --- | --- | --- |
| ファイルの変更を捨てて元に戻す | `git restore <ファイル>` | **戻せないので注意** |
| `add` を取り消す(変更は残す) | `git restore --staged <ファイル>` | |
| 直前のコミットメッセージを直す | `git commit --amend -m "新しいメッセージ"` | **push 前だけ** |
| 直前のコミットを取り消す(変更は残す) | `git reset --soft HEAD~1` | **push 前だけ** |
| push 済みのコミットを打ち消す | `git revert <コミットID>` | 打ち消すコミットを新たに積む。履歴を壊さない |
| 作業を一時退避する | `git stash` → 戻すときは `git stash pop` | ブランチを急いで切り替えたいとき |

**コンフリクト(競合)が起きたら**

```bash
git pull                     # ここで CONFLICT と表示される
# → エディタで <<<<<<< ======= >>>>>>> の箇所を手で直す(残す内容を決める)
git add <直したファイル>
git commit                   # マージコミットを作る(rebase 中なら git rebase --continue)

# 手に負えなくなったら中断して元に戻す
git merge --abort            # または git rebase --abort
```

### 8.5 コミットメッセージの書き方

`<種別>: <日本語で何をしたか>` の形にする。

| 種別 | 使う場面 |
| --- | --- |
| `feat` | 機能追加 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみの変更 |
| `refactor` | 挙動を変えないコード整理 |
| `test` | テストの追加 / 修正 |
| `chore` | 設定・依存関係・CI など |

```bash
git commit -m "feat: チャット履歴の保存を追加"
git commit -m "fix: 空メッセージ送信時に 500 になる問題を修正"
```

### 8.6 やってはいけないこと

| やってはいけないこと | 理由 / 代わりにすること |
| --- | --- |
| `main` に直接コミット / push | 必ずブランチを切って PR を出す(ブランチ保護で拒否される) |
| `git push --force` | 他人の履歴を壊す。保護設定でも拒否される。打ち消しは `git revert` |
| `.env` や `infra/secrets/*.json` をコミット | 資格情報の漏洩。`.gitignore` 済みだが `git add -f` で強制追加しない |
| `git reset --hard` を安易に使う | コミットしていない変更が**完全に消える**。まず `git stash` |
| 巨大な 1 コミット | レビュー不能。機能の区切りごとにコミットする |

> **もし `.env` をコミットしてしまったら**: push 前なら `git rm --cached backend/.env` してコミットし直す。
> push 済みなら履歴から消えないため、**該当する認証情報を GCP 側で無効化して作り直す**。

---

## 9. トラブルシューティング

| 症状 | 対処 |
| --- | --- |
| `GOOGLE_CLOUD_PROJECT が未設定です` | `backend/.env` にプロジェクト ID を設定する |
| 403 / PermissionDenied | `aiplatform.googleapis.com` の有効化と、SA への Vertex AI User ロール付与を確認 |
| フロントから API が呼べない(CORS) | `backend/app/core/config.py` の `cors_origins` に接続元 URL を追加 |
| コンテナでコード変更が反映されない | Windows では `WATCHFILES_FORCE_POLLING=true`(compose 設定済み)を確認 |
| `uv run pytest` がブロックされる | `uv run python -m pytest` を使う |
| `mypy` が `DLL load failed` で落ちる | ローカルのアプリ制御ポリシーによるもの。Docker または CI で型チェックする |
| Flutter コンテナのビルドが遅い | 開発中はネイティブ起動(4.2)を使い、compose は結合確認時に使う |
