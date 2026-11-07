# 申請内容の自動入力(App Store Connect・テキストのメタデータ)

**作る → 確認 → 入力** の流れ。AI が申請内容を作り、オーナーが差分を確認して OK したら、API で入力する。
**審査への提出は、自動にしない**(オーナーが App Store Connect の画面で、手で提出する)。

## 状態(重要)
- `asc_sync.py` のテスト(`python3 -m unittest -v test_asc_sync`)は、偽の応答で36件通過している。**実際の App Store Connect の API では、まだ一度も実行していない。**
- 最初は必ず `plan`(読み取りのみ)だけを実行し、結果を目で確認する。`apply` は、その後。
- API の細部(リソース名、状態の名前、文字数の上限)は、Apple の公式リファレンスで確認しながら使う。確認できた点: トークンは ES256、`aud` は `appstoreconnect-v1`、有効期間は20分以内(公式のフォーラム情報)、`PATCH /v1/appStoreVersionLocalizations/{id}` が存在する(公式リファレンス)。

**最初に実行する時は、`FIRST_RUN.md`(鍵の作成から `plan` までのチェックリスト)を順に確認する。**

## 自動にできるもの / できないもの
| 項目 | このスクリプト |
|---|---|
| バージョンの掲載文(説明、キーワード、プロモーション文、サポート/マーケティングURL、新機能) | 対応(差分の確認と反映) |
| アプリ情報(名前、サブタイトル、プライバシーポリシーURL) | 対応 |
| 審査メモ(notes) | 対応 |
| アプリのレコード作成 | **できない**(画面で作成。API に作成の呼び出しがないとされる) |
| ビルドのアップロード | 対象外(Xcode / Transporter。オーナーが指示した時だけ) |
| App Privacy(プライバシーの申告) | **対象外**(公開の API で確認できない。画面で手動) |
| 審査連絡先(姓名・メール・電話)、審査用アカウント | **対象外・手動**(個人情報。スクリプトは受け付けず、入力に含まれると止める) |
| スクリーンショット | **対応**(App Asset Library。下の節) |
| 年齢制限の回答 | **対応**(`ageRating`。下の節) |
| 価格 | **対応(初回の設定のみ・二段階の承認)**(`price`。下の節)。**既存の価格の変更は未対応(画面で変更)** |
| 配信地域 | **手動のまま**(2026-11-06 に公式で確認した結果は下の節) |
| **審査への提出** | **対象外・手動** |

## 配信地域(調査結果・手動のまま)
公式ドキュメント(2026-11-06)で確認できたこと:
- 読み取り: `GET /v2/appAvailabilities/{id}`、`.../territoryAvailabilities`(App Store Connect API 3.0.0 以降)。
- 書き込み: `POST /v2/appAvailabilities` は**「Create an app pre-order(事前注文の作成)」**で、説明は「事前注文を作り、公開予定日を設定する」。`PATCH /v1/territoryAvailabilities/{id}` は**「事前注文の地域の変更」**(「事前注文のリリース地域を更新する」)。`POST /v1/endAppAvailabilityPreOrders` は事前注文の終了。コレクションの説明も「事前注文のための地域と日付の設定を管理する」。
- `AppAvailabilityV2` は「アプリが利用できる地域とリリース日の設定」のオブジェクトだが、**属性の一覧は取得できなかった**(ページに本文なし)。
- **結論**: 公式の文面から確認できる書き込みの API は、事前注文用のみ。**通常の配信地域(どの国・地域で売るか)を設定できる API は、確認できなかった**。誤って地域を変えると販売に影響するため、**手動(App Store Connect の画面)のまま**にする。読み取りだけなら可能だが、現時点では必要性が低いので実装していない。

※ 実装する他の項目は、各エンドポイントの本文を確認してから、同じ関所(`plan` → OK → `apply`)で作る。

## 価格(`price`・初回の設定のみ)
- 公式(2026-11-06): 価格ポイントは `GET /v1/apps/{id}/appPricePoints`(`filter[territory]`、`limit`、ページ送り)。各価格ポイントは `customerPrice`(文字列。無料は `"0.0"`)と、不透明な ID を持つ。**ID は組み立てず、取得した値を使う。**現在の価格は `GET /v1/apps/{id}/appPriceSchedule` と、その `manualPrices`。設定は `POST /v1/appPriceSchedules`(基準の地域、手動の価格、開始日・終了日。Apple の例の形)。
- 入力: `"price": {"baseTerritory": "JPN", "customerPrice": "160.0", "startDate": null}`(地域は3文字のコード)。無料は `"0.0"`。
- `plan`: 価格ポイントを探して(なければ近い価格を表示して止まる)、現在の価格を読む。
- **二段階の承認**: ①`plan` の差分をオーナーが OK(通常の `apply`)。②**価格は、さらに `--confirm-price JPN=160` のように地域と金額を打ち直さないと、何も書き込む前に止まる。** 金額と地域が、承認した内容と一致しないと止まる。
- **対応は「新規の設定」のみ**。すでに価格が設定済みで、金額が違う場合は、誤って価格を壊さないよう、止まる(画面で変更)。同じ金額なら変更なし。
- 他の地域の価格は、Apple が基準の地域から自動で決める(App Store Connect の画面で確認)。税・手数料・販売地域の確認は、オーナー。

## 年齢制限の回答(`ageRating`)
- 公式(2026-11-06): 読み取り `GET /v1/appInfos/{id}/ageRatingDeclaration`、更新 `PATCH /v1/ageRatingDeclarations/{id}`(**変更する属性だけ**を送る)。審査提出の前に回答が必要。
- 属性名(公式の PATCH の例): `alcoholTobaccoOrDrugUseOrReferences`、`contests`、`gambling`(true / false)、`gamblingSimulated`、`medicalOrTreatmentInformation`、`profanityOrCrudeHumor`、`sexualContentGraphicAndNudity`、`sexualContentOrNudity`、`horrorOrFearThemes`、`matureOrSuggestiveThemes`、`unrestrictedWebAccess`(true / false)、`violenceCartoonOrFantasy`、`violenceRealisticProlongedGraphicOrSadistic`、`violenceRealistic`、`kidsAgeBand`(null または Made for Kids の年齢帯の文字列)。
- 値: 段階の属性は `NONE` / `INFREQUENT` / `FREQUENT`。**`INFREQUENT_OR_MILD` / `FREQUENT_OR_INTENSE` は非推奨**(入力で止まる)。
- **実際に受け付ける属性は、読み取った現在の回答のキーを正とする**(属性名が増減しても、現在の回答にない名前は止まる)。型が違う(真偽値の属性に文字列、など)場合も止まる。Apple は年齢区分の仕組みを更新することがあるため、App Store Connect の画面の質問と、API の属性が一致しているかを、`plan` の前に画面で確認する。
- **年齢制限は申告であり、アプリの実際の内容に基づく**。アルコール等を含むアプリは、該当する属性を正直に申告する。`kidsAgeBand`(Made for Kids)は、審査・広告・分析の制限が大きく変わるので、設計の段階でオーナーが決める。回答はオーナーが確認してから適用する。

## スクリーンショット(App Asset Library)
**Apple は、従来のセット方式(`appScreenshotSets` / `appScreenshots`)を非推奨にし、App Asset Library を後継とした**(公式ドキュメント、2026-11-06 確認)。このスクリプトは後継の方式で実装している。
流れ(公式の4段階): ①予約(`POST /v1/appAssetLibraryImages`。ファイル名・サイズ・カテゴリ `APP_SCREENSHOTS_AND_PREVIEWS`) → ②アップロード(返ってきた `uploadOperations` の URL に、指定の範囲のバイトを送る。**認証なし・期限つき**。URL は共有・表示しない) → ③確定(`PATCH` で `uploaded: true` だけ。**旧方式のチェックサムは不要**) → ④処理待ち(`PREPARE_FOR_SUBMISSION` になるまで確認。`FAILED` なら画像を削除してやり直し)。その後、**配置**(`POST /v1/appAssetLibraryPlacements`。種類 `APP_SCREENSHOT`、配置グループ、画像、対象のローカライズ)と、**並び順**(`POST /v1/appAssetLibraryPlacementOrderingRequests`)を行う。
- 入力: `screenshots: {ロケール: {配置グループ: [ファイルのパス, ...]}}`(`submission.example.json` 参照)。配置グループの識別子(例: `IPHONE_DYNAMIC_ISLAND_LARGE_PROFILE`)は列挙ではなく、参照データから読む。**ハードコードしない。**
- `plan` で、参照データ(`GET /v1/appAssetLibraryRefData`)から、配置グループの存在と、寸法の完全一致を検査する。アルファチャンネル(透過)のある画像は止める。1グループ最大10枚(公式。参照データの上限が正)。
- 既存の配置がある時は、**置き換えには `--allow-delete-placements` が必要**(配置を削除する。画像はライブラリに残る)。無いと、何も書き込む前に止まる。
- 途中で失敗したら、その場で止まる(作成済みの画像は、ライブラリに残る。`filter[state]=AWAITING_UPLOAD` で放置された予約を探して削除できる)。
- スクリーンショットの寸法・形式の最新は `GET /v1/appAssetLibraryRefData` が正(`appstore/screenshots.md`)。

## 方式
### 1. 半自動(既定): オーナーが自分の Mac で実行する
1. AI が `appstore/kit.md` から、`submission.json`(下の形式。`submission.example.json` を参照)を作る。
2. オーナーが `python3 appstore/automation/asc_sync.py plan submission.json` を実行する(読み取りのみ)。
3. 表示された差分を確認する。
4. 問題なければ `apply submission.json --confirm-bundle-id <Bundle ID>` を実行する。
5. App Store Connect の画面で内容を確認し、手動の項目を入力し、**審査へ提出を手で押す**。
鍵はAIに渡さない。

### 2. オーナーの Mac 上の Claude Code が実行する
**クラウドのセッションでは使わない**(秘密鍵を持てない設計のため)。Mac 上のセッションで、次の関所を守る。
1. オーナーが、API の実行を明示的に指示する。
2. AI が `plan` を実行し、**差分をオーナーに見せる**(読み取りのみ)。
3. **オーナーが、会話の中で明確に OK した後にだけ** `apply` を実行する(OK なしに実行しない。OK は差分ごとの内容に対するもの)。
4. 実行後、変更前の値のバックアップの場所を報告する。App Store Connect の画面での確認を、オーナーに依頼する。
5. 審査への提出は、AI は行わない。

## 認証と鍵の扱い(厳守)
- App Store Connect の「ユーザとアクセス > 統合 > App Store Connect API」で、API キーを作る。権限は、必要最小限にする。
- 環境変数: `ASC_KEY_ID`、`ASC_ISSUER_ID`、`ASC_KEY_PATH`(.p8 のパス)。**.p8 の鍵・Key ID・Issuer ID は、リポジトリにコミットしない。チャットに貼らない。ログに出さない。**
- .p8 は、リポジトリの外に置く。紛失・漏洩したら、App Store Connect で鍵を失効させる。
- 依存: `pip install pyjwt cryptography`。

## 安全装置
- `plan` は GET のみ。書き込まない。
- `apply` は `--confirm-bundle-id` が必須。入力の `bundleId` と一致しないと止まる。
- 編集できる状態(`PREPARE_FOR_SUBMISSION`、`DEVELOPER_REJECTED`、`REJECTED`、`METADATA_REJECTED`)のバージョンのみ。それ以外(審査中、公開中)は止まる。
- 文字数の上限を超えると止まる。対象外の項目や、メール・電話らしい文字列が入力に含まれると止まる。
- 変更前の値を `private/asc_backup_*.json`(コミットされない)に保存してから送る。戻したい時は、この値を入力に書き直して `apply` する。
- ロケールが App Store Connect にない場合は、作らずに通知する(画面で追加してから)。
- 既存のスクリーンショットの置き換えは、`--allow-delete-placements` が無いと実行しない。

## Google Play
実装済み。`stores/google-play/playstore/automation/README.md`。
