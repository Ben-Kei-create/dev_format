# Godot の書き出し手順と、ストアとの関係(初版)

確認時点: 2026-11-06。Godot の最新安定版は 4.6.3 とされる(集計サイトの情報。公式の godotengine.org/download で確認)。4.7 は前版(プレリリース)。ライセンスは MIT とされる(二次情報。公式で確認)。
**エディタとエクスポートテンプレートのバージョンは、必ず一致させる**(不一致は、最初の書き出し失敗の典型的な原因とされる)。

## 共通
- 書き出しの前に、`review_prompts/`(ストア別)の段階2の確認を済ませる。
- 書き出し(Archive・アップロード・本番公開用のビルド)は、オーナーが実装完了を宣言し、指示した時だけ。
- 素材の出典とライセンスは `docs/asset_list.md`。
- プロジェクト設定: アプリ名、パッケージ名(Bundle ID / Application ID)、バージョン、向き、アイコン、セーフエリアを確認する。

## iOS(Apple)
公式ドキュメント「Exporting for iOS」で確認した点:
- **macOS で、Xcode をインストールしている必要がある。**
- エクスポートテンプレートを、Editor > Manage Export Templates からダウンロードする。
- 書き出しの設定で、**App Store Team ID(10文字のコード)と Bundle Identifier は必須**。空だと書き出しがエラーになる。Bundle ID は、英数字・ハイフン・ピリオドのみで、逆ドメイン形式を推奨。
- 書き出しは、**Xcode プロジェクトを生成する**。それを Xcode で開いて、通常の iOS アプリと同じようにビルド・Archive する。変更したら再度書き出す。
- iOS シミュレータは Compatibility レンダラーのみ対応。**実機で確認する。**
- コンパイルエラーが出る時は、`xcode-select` が Xcode を指しているか確認する。
- **プライバシーマニフェスト(要確認)**: Apple は 2024-05-01 以降、使用理由の申告が必要な API を使うアプリの審査を通さないとされる。Godot の iOS 書き出しの設定には、`privacy/` の項目(カメラ等の使用説明、収集するデータの分類)がある。ただし、**PrivacyInfo.xcprivacy を自動で生成するか、必要な API の理由を宣言できるかは、確認できなかった。**書き出した Xcode プロジェクトに PrivacyInfo.xcprivacy が含まれているかを確認し、含まれていなければ、自分で追加する。広告などのプラグインの SDK のマニフェストも確認する。結果を `stores/apple` の提出前チェック(App Privacy との一致)に反映する。
- 以降の申請(審査メモ、スクリーンショット、TestFlight、提出前チェック)は `stores/apple/` に従う。

## Android(Google Play)
公式ドキュメント「Exporting for Android」で確認した点(2026-11-06。stable 版):
- **JDK は OpenJDK 17 を推奨**(新しい JDK も対応するが、17 が最も互換性・安定性が高いとされる)。
- Android SDK の構成: Platform-Tools 35.0.0 以降、Build-Tools 35.0.1、Platform は Android 35、Command-line Tools は最新、CMake 3.10.2.4988404、NDK r28b。Editor Settings > Export > Android で、JDK と SDK のパスを設定する(全プロジェクト共通)。
- **AAB で書き出すには、Gradle ビルドの設定が必要**。「2021年8月以降に Google Play へ新しく出すアプリは AAB でなければならない」と書かれている。
- リリース用の**キーストア**: `keytool` で生成(`-keystore`、`-alias`、`-keyalg RSA`)。書き出し設定の Release にキーストアのパス、Release User にエイリアス、Release Password にパスワードを設定する。**キーストアのパスワードと鍵のパスワードは、現状同じにする必要がある。**リリースの書き出しでは「Export With Debug」のチェックを外す。AAB / APK のアップロードには、デバッグ用ではないキーストアが必要。
- **キーストアとパスワードは、リポジトリにコミットしない。チャットにも出さない。紛失すると更新ができなくなる。安全な場所に控える。**
- **ターゲット API レベル(2026-11-06 に調査)**: 2026-08-31 以降、新規アプリと更新は Android 16(API 36)以上が対象(`stores/google-play/`)。
  - Godot の書き出し設定には `gradle_build/min_sdk` と `gradle_build/target_sdk` がある(公式クラスリファレンス EditorExportPlatformAndroid。どちらも文字列。**既定値の記載はない**)。いずれも「Gradle ビルドの時に使う」と書かれているので、**`gradle_build/use_gradle_build` を有効にしたカスタムビルドで使う**。
  - 既定値(2026-11-06 に再調査): **4.7 は Target SDK 36 が既定**(フォーラムの報告。書き出し設定の表示は「36 (default)」、`DEFAULT_TARGET_SDK_VERSION` というソース上の定数がある)。**4.6.2 の APK の公開情報(第三者の配布サイト)は Target が Android 15(API 35)**で、4.6.x の既定は 35 とみなす(公式の記載は確認できず)。そのため、**4.6.x 以前では `Target SDK` を明示的に 36 にする**。3.6.3 の保守リリースでも既定が 36 に上がった。
  - 手順: ①使う Godot のバージョンで、`gradle_build/target_sdk` を**明示的に 36 にする** ②Android SDK Manager で、Platform 36 を入れる(公式のセットアップ一覧は Platform 35 までの記載で、古い可能性がある。ビルドエラーが出たら、新しい Godot へ上げる) ③AAB を書き出し、**中のマージ後のマニフェストに `android:targetSdkVersion="36"` が入っているか確認する**(AAB の中のマニフェストは `base/manifest/AndroidManifest.xml`。バイナリなので、テキスト検索では見つからない。Android Studio の APK Analyzer か、Play Console の App bundle explorer で開く) ④Play Console のアップロード後の警告も確認する(マニフェストが正しくても、Play が警告を出した例の報告がある)。
  - 満たせない場合は、Godot を新しいバージョンへ上げる。上げる時は、エディタとエクスポートテンプレートを一致させ、実機で再確認する。
- 以降の申請(クローズドテスト、掲載情報、データセーフティ、提出前チェック)は `stores/google-play/` に従う。

## 両ストアに出す時
- 同じ Godot プロジェクトから、Apple と Google Play の両方に出す場合も、**ストアごとに別のアプリとして申請**する。
- 体験・名前・見た目を明確に変える必要はないが、**同じアプリを別の名前で複数出さない**(Apple 4.3 / Google の Repetitive Content)。
- 広告・課金・プライバシーの申告は、ストアごとに実装と一致させる(Apple の App Privacy / Google のデータセーフティ)。

## 確認項目
- [ ] エディタとエクスポートテンプレートのバージョンが一致している
- [ ] 実機(iPhone / Android)で、最後まで動作を確認した
- [ ] セーフエリア、向き、画面サイズ、タッチ操作が問題ない
- [ ] 音量・バックグラウンド復帰・オフラインの挙動が問題ない
- [ ] 広告プラグインのライセンス・同意管理・申告への影響を確認した
- [ ] 素材のライセンスを `docs/asset_list.md` に記録した
- [ ] キーストア・証明書・パスワードがリポジトリに入っていない

## プロジェクトの詳細ルール(`CLAUDE.md` の要点の詳細)
- 2D・3D ゲームの標準エンジン(`philosophy/tech_standards.md`)。**書き出し先のストアのルールが、そのまま適用される**(App Store → `stores/apple/`、Google Play → `stores/google-play/`)。Godot は作り方であり、審査・ポリシーの対象は変わらない。
- 書き出しの手順・設定・ストアとの関係は `workflow/godot_export.md`。ビルドのバージョンは、エディタとエクスポートテンプレートを必ず一致させる。
- Android 向けは、**`gradle_build/target_sdk` を明示的に API 36 以上にし、書き出した AAB のマニフェストで確認する**(2026-08-31 以降の要件。`workflow/godot_export.md`)。
- iOS 向けの書き出しには macOS と Xcode が必要。書き出し(Xcode プロジェクトの生成、Archive、アップロード)は、**オーナーが実装完了を宣言し、指示するまで行わない**(テスト配布は、指示された時だけ)。
- 素材は `workflow/tools_catalog.md`(Kenney、Poly Haven、Quaternius、Mixamo、Pixelorama、Godot Asset Library)を第一候補にする。**Godot Asset Library はアセットごとにライセンスが違う。**個別に確認して `docs/asset_list.md` に記録。
- 起動時アニメーションは Godot 内で実装する(`modes/launch_animation.md`)。OS の起動画面と、エンジンの起動スプラッシュ(ロゴ)の扱いは、プロジェクト設定で確認する。
- 広告(AdMob など)は、Godot 用のプラグインを使う場合、**プラグインのライセンス・SDK のバージョン・同意管理(UMP / ATT)・プライバシー申告への影響を確認してから**採用する。
- 画面サイズ・向き・ノッチ(セーフエリア)・タッチ操作・文字の拡大・音量・バックグラウンド復帰を、実機で確認する。

