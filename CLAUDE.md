# CLAUDE.md

Claude Code がこのリポジトリで作業するときのルール。

## 0. 最優先ルール: README を読む / 直す

- **作業開始時、必ず [README.md](README.md) を読む。** 構成・起動手順・アーキテクチャ・SPEC 運用の「正」は README。
  記憶や推測ではなく README の記述に従う。
- **README と実際のコードが食い違っていたら、その場で README を直す**(またはユーザーに確認する)。放置しない。
- 以下を変更したら、**同じ変更の中で README も更新する**:
  - ディレクトリ構成 / レイヤ構成(§2)
  - 依存ライブラリ・技術スタック(§1)
  - 環境変数・認証方法(§3)
  - 起動コマンド・ポート・compose 構成(§4)
  - テスト / 静的解析のコマンド、CI の構成(§5)
  - 機能の追加・完了(§6 の機能一覧)
  - 新たに踏んだ環境依存の落とし穴(§9 トラブルシューティング)
- 作業の最後に「README の更新が必要な変更をしたか」を必ず自己点検し、更新した箇所(または不要と判断した理由)を報告する。

## 1. SPEC 駆動開発

機能開発は `docs/spec/<連番>-<機能名>/` の 3 点セットに沿って進める(運用の詳細は [docs/spec/README.md](docs/spec/README.md))。

| 段階 | 成果物 | 次に進む条件 |
| --- | --- | --- |
| 要件 | `requirements.md` | ユーザーの承認 |
| 設計 | `design.md` | ユーザーの承認 |
| 分解 | `tasks.md` | ユーザーの承認 |
| 実装 | コード + テスト | tasks が全て完了 |

守ること:

- **段階を飛ばさない。** 実装依頼を受けても、対応する spec が無ければ先に spec を作る(または「どの spec に属するか」を確認する)。
- requirements に書かれていない機能を design / 実装で勝手に足さない。必要だと思ったら提案して承認を得る。
- 実装中に設計を変えたら `design.md` を更新する。完了したタスクは `tasks.md` のチェックボックスを `- [x]` にする。
- spec フォルダ名は `_template/` をコピーし、連番 + kebab-case の機能名にする(例: `002-chat-history`)。

## 2. コーディング規約

### バックエンド(`backend/`)

- パッケージ管理は **uv** のみ。`pip install` は使わない。追加は `uv add <pkg>`(開発用は `uv add --dev <pkg>`)。
- レイヤの責務(README §2.2)を守る:
  - `api/routes/` は検証と HTTP 変換のみ。ビジネスロジックを書かない。
  - `services/` は FastAPI に依存しない。`HTTPException` を投げず、業務例外(例: `GeminiError`)を投げる。
  - 外部 API 呼び出しは必ず `services/` に閉じる。
- 設定値のハードコード禁止。`app/core/config.py` の `Settings` に追加し、`.env.example` にも項目を足す。
- 型注釈を必ず付ける。公開関数には docstring(日本語)を書く。
- 新しいルータは `app/api/router.py` に登録する。

### フロントエンド(`frontend/`)

- 機能単位で `lib/features/<機能>/` に閉じる。画面から直接 `http` を呼ばず、Repository → `core/api_client.dart` を経由する。
- 接続先 URL をハードコードしない。`lib/core/app_config.dart`(`--dart-define`)を使う。
- `flutter analyze` の警告を残さない。

### 共通

- 秘匿情報(API キー、サービスアカウントキー)をコミットしない。`backend/.env` と `infra/secrets/` は Git 管理外。
- コメント・ドキュメント・コミットメッセージは日本語。

## 3. 検証コマンド

コードを変更したら、関係する側を必ず実行して結果を報告する。

```bash
# backend
cd backend && uv run python -m pytest && uv run ruff check . && uv run ruff format .

# frontend
cd frontend && dart format . && flutter analyze && flutter test
```

push 後は GitHub Actions([.github/workflows/ci.yml](.github/workflows/ci.yml))が
ruff / **mypy** / pytest / dart format / flutter analyze / flutter test / docker build を実行する。
CI と同じ内容をローカルでも通してから push すること(mypy はローカルで動かない場合があるため CI 結果を確認する)。
CI のステップを増減したら README §5.2 も更新する。
ジョブ名(`backend` / `frontend` / `docker`)はブランチ保護の必須チェック名と一致しているため、
変更するとルールセットが機能しなくなる。変更する場合は README §5.3 の手順も合わせて直すこと。

- `uv run pytest` は Windows のアプリケーション制御ポリシーでブロックされることがあるため、
  **`uv run python -m pytest`** を使う。
- 外部 API(Gemini)を叩くテストは書かない。`dependency_overrides` / フェイク Repository でスタブ化する。

## 4. Git

- ブランチは spec に対応させる: `feat/<連番>-<機能名>`。`main` に直接コミットしない。
- コミットは論理単位で分ける。README / spec の更新は、対応するコード変更と同じコミットに含める。
- コミットメッセージは `<種別>: <日本語の説明>`(種別は `feat` / `fix` / `docs` / `refactor` / `test` / `chore`)。
- コミット・push はユーザーに依頼されたときだけ行う。
- ユーザーに Git 操作を案内するときは README §8「Git コマンド一覧」の書式・方針に合わせる
  (手順を新しく案内したら §8 にも追記する)。

## 5. やる前に確認すること

- 既存の公開 API(エンドポイントのパスやスキーマ)を変更するとき
- 依存ライブラリの追加、アーキテクチャ方針の変更
- spec に書かれていない機能の追加
- `docker compose down -v` などデータを消す操作
