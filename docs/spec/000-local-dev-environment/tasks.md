# 実装タスク: ローカル開発環境の整備

- 対応する設計: `./design.md`
- 進捗: 8 / 9

## タスク一覧

### バックエンド

- [x] **T-01: uv プロジェクト初期化**
  - 変更対象: `backend/pyproject.toml`, `backend/uv.lock`
  - 完了条件: `uv sync` が成功する
- [x] **T-02: 設定 / ロギング基盤**
  - 変更対象: `backend/app/core/`
  - 完了条件: `.env` の値が `get_settings()` に反映される
- [x] **T-03: FastAPI アプリと health / chat エンドポイント**
  - 変更対象: `backend/app/main.py`, `backend/app/api/`
  - 完了条件: `uv run python -m pytest` が通る / 関連 AC: AC-2
- [x] **T-04: Gemini サービス(Vertex AI)**
  - 変更対象: `backend/app/services/gemini.py`
  - 完了条件: `.env` 設定時に `/api/v1/chat` が応答を返す / 関連 AC: AC-4
  - 備考: 実装済み。Vertex AI への到達までは確認済みだが、実プロジェクト ID での応答確認は未実施

### フロントエンド

- [x] **T-05: Flutter プロジェクト作成と API クライアント**
  - 変更対象: `frontend/lib/core/`
  - 完了条件: `flutter analyze` がエラー 0 件
- [x] **T-06: チャット画面とウィジェットテスト**
  - 変更対象: `frontend/lib/features/chat/`, `frontend/test/`
  - 完了条件: `flutter test` が通る / 関連 AC: AC-3

### 結合 / 仕上げ

- [ ] **T-07: Dockerfile と docker-compose**
  - 変更対象: `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`
  - 完了条件: `docker compose config` が通り、`docker compose up` で両サービスが起動する / 関連 AC: AC-1
  - 備考: ファイル作成と `docker compose config` は完了。イメージビルド込みの実起動確認が残っている
- [x] **T-09: CI(GitHub Actions)の構築**
  - 変更対象: `.github/workflows/ci.yml`
  - 完了条件: push / PR で backend(ruff・mypy・pytest) / frontend(format・analyze・test) / docker の 3 ジョブが実行される
  - 関連 AC: AC-6
- [x] **T-08: ドキュメント整備**
  - 変更対象: `README.md`, `CLAUDE.md`, `docs/spec/`
  - 完了条件: spec テンプレートが揃い、README にアーキテクチャと起動手順が書かれている / 関連 AC: AC-5
