# dev_format

新しいアプリを作る時に使う、開発フォーマット集。App Store のリジェクト(4.3 重複・スパム、4.2.6 テンプレート等)を避けるための、段階別チェックと記録テンプレートを入れている。

## 中身(`template/`)
- `CLAUDE.md`: Claude Code が起動時に読む開発ルール
- `review_prompts/`: 審査チェック指示文(1 企画時 / 2 開発中 / 3 提出前)
- `docs/`: 開発ログ、競合メモ、TestFlight 記録、審査返信の下書き
- `appstore/`: App Store Connect 申請キット作成指示書、アプリ固有の入力欄
- `private/`: 個人情報の置き場(.gitignore で除外。見本のみ入っている)
- `.gitignore`: 個人情報・鍵類をコミットしない設定

## 新規アプリへの導入
```bash
git clone https://github.com/Ben-Kei-create/dev_format
cd dev_format
./setup.sh /path/to/new-app-repo
```
コピー後、`private/owner_info.md` に実際の値を入れる(コミットされない)。その後、新規アプリのリポジトリでコミットする。既に `CLAUDE.md` がある場合は、`template/CLAUDE.md` の内容を追記する。

## 更新
チェック項目を改善したら、このリポジトリを更新し、使っているアプリ側にも再度コピーする。
