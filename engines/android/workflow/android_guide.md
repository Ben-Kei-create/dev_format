# Android ネイティブの詳細ルール(初版。公式で要確認の項目あり)

`CLAUDE.md` の要点の詳細版。**公式(developer.android.com)で確認した点には(公式)、二次情報や未確認の点には(要確認)と付ける。**確認日 2026-11-06。

- **標準**: Kotlin + Jetpack Compose。UI は Compose を基本とし、画面ごとに状態(ViewModel + StateFlow)を持つ。迷ったら公式の「Guide to app architecture」(developer.android.com)に従う。
- データは**端末内保存を優先**(設定は DataStore、構造化データは Room)。バックエンドは、必要性が明確になるまで入れない(`philosophy/tech_standards.md`)。
- 依存を増やさない(「機能は削る」)。DI(Hilt など)や外部ライブラリは、必要が明確な時だけ。
- **ターゲット API レベル**: 2026-08-31 以降、新規アプリと更新は Android 16(API 36)以上(`stores/google-play/`)。minSdk は、対象ユーザーの端末の分布を見て決め、理由を `docs/design_brief.md` に書く。
- ビルド形式は Android App Bundle(AAB)。リリース用のキーストアとパスワードは、**リポジトリにコミットしない・チャットに出さない**。
- フォントは `res/font` に入れ、サイズは `sp` で指定する(端末の文字サイズ設定に追従)。`philosophy/fonts.md` の固定リストのみ。
- アクセシビリティ: TalkBack のラベル、十分なコントラスト、タップ領域(48dp 以上を目安)、文字拡大。
- 起動: OS の起動画面(Android 12 以降のスプラッシュ。背景色とアイコン)は静止。パラパラ漫画のアニメーションは、その直後に Compose 内で流す(`modes/launch_animation.md`)。「アニメーションを減らす」設定(アニメーション倍率が 0)の時は、最後のフレームを静止で表示する。
- スクリーンショットは `stores/google-play/playstore/screenshots.md` に従い、エミュレータまたは実機で撮る。
- テスト: 実機で、複数の画面サイズ・Android バージョン・向き・ダークモード・文字拡大を確認する。


## 公式で確認した内容(2026-11-06)

### アーキテクチャ(App architecture)
- 最低2層: **UI 層**(画面に表示)と**データ層**(ビジネスロジックを持ち、データを公開)。**ドメイン層は任意**で、複雑なロジックや再利用が必要な時だけ使う。(公式)
- UI 層は Jetpack Compose の関数 + **状態保持クラス(ViewModel など)**。状態保持クラスは、その UI と同じ期間だけ生きる(画面なら、バックスタックから外れるまで)。(公式)
- データ層は**リポジトリ**(データの種類ごとに1つ)と、0個以上の**データソース**(ファイル、ネットワーク、ローカル DB)。(公式)
- 原則: **関心の分離**、**データモデルから UI を駆動**(できれば永続化したモデル。オフラインでも動く)、**単一の信頼できる情報源(SSOT)**、**単方向のデータの流れ(UDF)**(状態は下へ、イベントは上へ)。(公式)
- Activity にデータや状態を持たせない。単一 Activity で Compose の画面を載せる構成が現代的。(公式)
- **DI(依存性注入)は Hilt を使うことが公式の推奨(Key Point)。**本フォーマットの「依存を増やさない」(機能は削る)と食い違う。**小さなアプリは、手動の DI(コンストラクタで渡す)で足りる。規模が増えたら Hilt を入れる、という扱いを既定にする。**オーナーが違う方針なら、変更する。

### Compose の状態(Compose state)
- 状態は `remember { mutableStateOf(...) }` / `by`。**画面の回転などの構成変更をまたぐ値は `rememberSaveable`**。(公式)
- **ViewModel の `StateFlow` は `collectAsStateWithLifecycle()` で集める。公式が「Android アプリでフローを集める推奨の方法」と明記。**依存: `androidx.lifecycle:lifecycle-runtime-compose`(公式の表記は 2.11.0)。(公式)
- **状態の持ち上げ(state hoisting)**: 値を `value: T` と `onValueChange: (T) -> Unit` の2つの引数にして、呼び出し側へ状態を移す。持ち上げ先は、(1)読む全ての composable の最も近い共通の親、(2)変更される最も高い場所、(3)同じイベントで変わる2つの状態は一緒に、の3つの規則。(公式)
- **`ArrayList` や `mutableListOf()` のような、観測されない可変オブジェクトを状態にしない。**`State<List<T>>` と不変の `listOf()` を使う。(公式)
- 基本の形:
  ```kotlin
  // ViewModel: 状態は不変の data class を StateFlow で公開し、イベントは関数で受ける
  // 画面:
  @Composable
  fun HomeRoute(vm: HomeViewModel = viewModel()) {
      val state by vm.uiState.collectAsStateWithLifecycle()
      HomeScreen(state = state, onAnswer = vm::onAnswer)   // 状態は下へ、イベントは上へ
  }
  @Composable
  fun HomeScreen(state: HomeUiState, onAnswer: (Int) -> Unit) { /* 状態を持たない(ステートレス) */ }
  ```

### スプラッシュ画面(起動)
- **Android 12 以降は、アプリの起動時に OS がスプラッシュ画面を出す**(アプリのアイコン + 単色の背景)。Jetpack の `SplashScreen` 互換ライブラリ(`androidx.core:core-splashscreen`、公式の表記は 1.2.0)で、API 23 以降に同じ見た目を提供でき、Compose でも使える。(公式)
- 使い方: スプラッシュ用のテーマ(`Theme.SplashScreen`)を作り、`postSplashScreenTheme` を設定し、開始 Activity で `installSplashScreen()` を **`super.onCreate()` の前**に呼ぶ。(公式)
- スプラッシュは**最初のフレームが描画されるまで**出る。非同期の読み込みがある時は `setKeepOnScreenCondition { ... }` で残す(条件は描画のたびに評価されるので、速くする)。(公式)
- アイコンは**アニメーションにもできる**(AnimatedVectorDrawable。**推奨は 1,000ms 以内**。開始の遅延は 166ms まで)。終了のアニメーションは `setOnExitAnimationListener` で変えられ、終わったら `remove()` を呼ぶ。(公式)
- スプラッシュは**ホットスタートでは出ない**。(公式)
- **本フォーマットとの関係**: OS のスプラッシュは短い静止(または短い AVD)にとどめ、「パラパラ漫画」(`modes/launch_animation.md`)は、スプラッシュが消えた後に Compose 内で流す。スプラッシュのアイコンは、既定でランチャーのアイコンになる(OS の仕様)。「アイコンの図柄を他へ流用しない」は、パラパラ漫画の側で守る。
- 「アニメーションを減らす」設定の検出(アニメーション倍率が 0)は、今回の公式ページでは確認できなかった(要確認)。

### アクセシビリティ
- Compose と Material の部品は、アクセシビリティの既定の動作を持つ。`Button` / `Switch` / `Checkbox` などの標準部品を使う。(公式)
- ボタンや画像などの操作できる要素には、**意味の分かるラベル**(`contentDescription` / `semantics`)を付ける。装飾だけの画像は `contentDescription = null`。(公式)
- **色だけに頼らない**(形・文字・位置も使う)。(公式)
- ドラッグやスワイプでしかできない操作には、**代替の操作(`customActions`)**を用意する。(公式)
- **タップ領域は 48dp(公式の API defaults ページ: Material のアクセシビリティの指針に従う)。**Button / IconButton / ListItem、およびタップできる状態の Checkbox / RadioButton / Switch / Slider / Surface などの Material 部品は、この最小サイズを内部で保っている。**自作のタップできる要素は自分で確保する**: 見た目は小さいまま、タップ領域だけ広げるには `Modifier.minimumInteractiveComponentSize()`(Material 3。レイアウト上で各方向に最低 48dp を確保し、中央に置く)を使うか、`sizeIn` で十分な最小サイズを指定する。隣のタップ領域と重ならないようにする。マウスなどの細かい入力では、これより小さくてよい。(公式)
- コントラスト比の具体的な数値は、今回取得したページには載っていなかった(要確認。WCAG の基準を使う)。


### ローカルのデータ保存(Room と DataStore)(公式、2026-11-06)
- **Room**: SQLite の上の抽象層。SQL のコンパイル時検証、定型コードの削減、移行の簡素化。**SQLite の API を直接使うより Room を推奨**(公式)。構成は、データベースのクラス、エンティティ、DAO の3つ。アプリが単一プロセスなら、データベースのインスタンスはシングルトンにする(1つが重い)。**公式ページの例は `androidx.room3`(Room 3.0.3)で、KSP が必要**(バージョンと座標は公式で確認してから入れる)。
- **DataStore**: キーと値、または型つきのオブジェクトを保存する。Kotlin のコルーチンと Flow で、非同期・一貫・トランザクションで動く。**`SharedPreferences` を使っているなら DataStore への移行を検討**(公式)。Preferences DataStore(`androidx.datastore:datastore-preferences`、公式の表記は 1.3.0)は、スキーマ不要のキー・値。
- **使い分け(公式)**: **小さなデータは DataStore。大きい・複雑なデータ、部分的な更新、参照整合性が要るなら Room。** DataStore は部分更新も参照整合性もサポートしない。
  → 本フォーマットでは、設定・小さな状態は DataStore、構造化データ(問題・履歴など)は Room、を既定にする。
- **DataStore の規則(公式)**: 同じファイルに対して、1プロセスで DataStore のインスタンスを2つ以上作らない(例外になる)。保存する型は不変(immutable)にする。**Compose アプリでは、DataStore の読み書きはデータ層(リポジトリ)に置き、ViewModel の `StateFlow` として UI に渡す。composable の中で直接読み書きしない。**
- **バックアップ**: DataStore のファイルは、既定で Android の自動バックアップと端末間の移行の対象になる(公式)。機微なデータは別のファイルに分け、`data_extraction_rules.xml` で除外する。→ データセーフティ・プライバシーの申告と一致させる。

### 「アニメーションを減らす」設定の検出(公式、2026-11-06)
- システムの設定値 `Settings.Global.ANIMATOR_DURATION_SCALE`:「Animator ベースのアニメーションの倍率。**0.0f だとアニメーションが即座に終わる**。既定は 1.0f」(公式)。
- **API 33 以降は `ValueAnimator.getDurationScale()` で、システム全体の倍率を取得できる**。倍率の変更を監視する登録の API もある(公式)。
- Compose のアニメーションは、1.2.0 から、開発者向けオプションの「アニメーターの長さのスケール」に従う(公式)。
- **注意**: 本フォーマットの「パラパラ漫画」(`modes/frame_animation.md`)は、自前のタイマーでフレームを切り替えるため、**この倍率を自動では守らない**。倍率が 0 の時は、最後のフレームを静止で表示するよう、**自分で判定する**(API 33 以降は `ValueAnimator.getDurationScale() == 0f`。それ未満は `Settings.Global.ANIMATOR_DURATION_SCALE` を読む)。
- 設定画面の「アニメーションを削除(Remove animations)」のトグルが、この倍率を 0 にするかどうかは、今回の公式ページでは確認できなかった(要確認)。実機で、トグルを入れてから倍率が 0 になるかを確かめる。
