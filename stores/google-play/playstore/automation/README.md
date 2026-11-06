# 申請内容の自動入力(Google Play・掲載情報・画像・データセーフティ)

**作る → 確認 → 入力** の流れ。AI が申請内容を作り、オーナーが差分を確認して OK したら、API で入力する。
**確定(`--commit`)は、別の承認を得てから。** 確定は「変更を公開に送る」操作(公開済みのアプリでは審査に送られる)。

## 状態(重要)
- `play_sync.py` のテスト(`python3 -m unittest -v test_play_sync`)は、偽の応答で12件通過している。**実際の Google Play の API では、まだ一度も実行していない。**
- 最初は必ず `plan` だけを実行する。
- 公式リファレンスで確認できた点(2026-11-06): `applications.dataSafety`(POST。本文は `safetyLabels` = CSV の内容、応答は空、スコープ `androidpublisher`)、`edits.commit`(POST `.../edits/{editId}:commit`。`changesInReviewBehavior` の `ERROR_IF_IN_REVIEW` あり。`changesNotSentForReview` あり)、`edits.listings` の `list/get/update/patch/delete/deleteall` と Listing の項目(`language`、`title`、`fullDescription`、`shortDescription`、`video`)、`edits.images.upload`(アップロード URI は `upload/androidpublisher/v3/applications/{packageName}/edits/{editId}/listings/{language}/{imageType}`)。
- **未検証**: `edits.listings` の HTTP 動詞(公式ページに明記がなく、`patch` は PATCH とした)、`imageType` の値(公式ページに一覧がなく、`phoneScreenshots` / `icon` / `featureGraphic` とした)、`edits.insert` / `edits.delete` / `edits.validate` の細部、画像の枚数・寸法の上限。エラーが出たら、公式の AppImageType と各ページを確認する。

## 自動にできるもの / できないもの
| 項目 | このスクリプト |
|---|---|
| 掲載情報(タイトル、短い説明、詳しい説明、動画URL) | 対応 |
| 画像(スクリーンショット、アイコン、フィーチャーグラフィック) | 対応(置き換えは `--allow-delete-images` が必要) |
| データセーフティ(CSV) | 対応(`datasafety`。**現在の値を API で読めないので差分はなし。宣言全体を上書き**) |
| アプリの作成、AAB のアップロード、トラックへのリリース | 対象外(手動 / 別の工程) |
| アプリのコンテンツの宣言(広告、アクセス、ターゲット層、レーティング) | 対象外(手動) |
| 連絡先(メール・電話など)、個人情報 | **対象外・手動**(入力にメール・電話らしい文字列があると止まる) |
| 確定(公開に送る) | `--commit`(**別の承認を得てから**) |

## 方式
1. 半自動(既定): AI が `playstore/kit.md` から `play.json`(`play.example.json` 参照)を作る。オーナーが自分の端末で `plan` → 差分を確認 → `apply`。
2. オーナーの Mac 上の Claude Code: オーナーの明示的な指示 → `plan` → **差分を見せる** → **会話で明確な OK** → `apply`。確定(`--commit`)は、さらに別の承認。**クラウドのセッションでは使わない**(サービスアカウントの鍵を持てない設計のため)。

## 使い方
```bash
export PLAY_SA_KEY_PATH=/安全な場所/service-account.json   # リポジトリの外。コミットしない・貼らない
python3 playstore/automation/play_sync.py plan play.json
python3 playstore/automation/play_sync.py apply play.json --confirm-package com.example.app            # サーバーで検証して、下書きは破棄(確定しない)
python3 playstore/automation/play_sync.py apply play.json --confirm-package com.example.app --commit   # 確定(別の承認を得てから)
python3 playstore/automation/play_sync.py datasafety play.json --confirm-package com.example.app       # データセーフティの CSV を送信
```

## 認証と鍵の扱い(厳守)
- Google Cloud でサービスアカウントを作り、Play Console の「ユーザーと権限」で招待して、必要最小限の権限を与える。Android Publisher API を有効にする。
- **サービスアカウントの JSON 鍵は、リポジトリにコミットしない。チャットに貼らない。ログに出さない。**リポジトリの外に置く。漏洩したら、鍵を失効させる。
- 依存: `pip install pyjwt cryptography`。

## 安全装置
- `plan` は読み取りのみ(下書きを作って読み、破棄する)。
- `apply` は `--confirm-package` が必須。`--commit` が無ければ、検証だけして下書きを破棄する。
- 確定は `changesInReviewBehavior=ERROR_IF_IN_REVIEW`(審査中の変更がある時は、取り消さずにエラーにする)。
- 既存の画像の置き換えは `--allow-delete-images` が無いと、何も作らずに止まる。
- 文字数の上限、対象外の項目、メール・電話らしい文字列で止まる。
- 途中で検証に失敗したら、下書きを破棄し、確定しない。

## データセーフティの CSV
Play Console から、現在のテンプレート(CSV)をダウンロードして、AI が実装(コード・SDK)に基づいて回答を整理する(`playstore/app_content_and_data_safety.md`)。内容は必ずオーナーが確認する。API の CSV 形式は、公式のヘルプ(Play Console のデータセーフティの CSV)に従う。
