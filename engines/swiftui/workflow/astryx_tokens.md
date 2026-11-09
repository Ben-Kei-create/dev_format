# Astryx(Meta 製デザインシステム)を SwiftUI で使う場合

調査: 2026-11-09、`github.com/meta/astryx`(MIT)を読み取りで確認。**ビルドや Swift のコンパイルは実行していない。**
Astryx 本体は React 19 + StyleX の Web 用。SwiftUI 用は `packages/native/apple` にあるが、**実験段階(Experimental / canary のみ。公式が「本番アプリ向けではない」と明記)**。

## 方針(既定)
- **丸ごと採用しない。トークン(色・余白・文字サイズ)の考え方と、必要な時だけ一部を借りる。**
  理由: 依存を最小に保つ方針、部品が少ない(約12。Web は150以上)、APIが予告なく変わる、既製テーマのままだとアプリが似て見える(4.3 / 4.2.6)。
- 採用するかは、オーナーに質問して決める(`modes/conversation_style.md` の形態に従う)。

## 公式 README から確認できたこと
- Swift パッケージ名 `AstryxNative`。製品は `Astryx`(SwiftUI の部品)と `AstryxNative`(契約型・ロジックホスト)。対応は iOS 17 以上、macOS 14 以上。
- 部品: Text, Heading, Button, TextInput, Card, Banner, Icon, Avatar, List, Thumbnail, Tooltip ほか。ログインのテンプレート(`Templates/Login/`、コピーして自分のものにする)。
- テーマ: `astryxTheme(_:)` で部分木に適用。`astryx.tokens.color.textPrimary`、`tokens.space.s4`、`tokens.font.body.size` のように型つきで読める。文字は Dynamic Type と Dark Mode に従う。7つの既製テーマ(neutral, butter, chocolate, matcha, stone, gothic, y2k)と default が生成済み。
- アイコンは SF Symbols に対応づけ(テーマで別のシンボルやアプリ内画像に差し替え可)。
- フォントは、テーマの `font-family-*` の最初の使える1つが選ばれる。システムフォントは `-apple-system` などで指定。

## 私の推測(要確認)
- `Package.swift` が `packages/native/apple/` にあり、リポジトリの根にはない。→ **URL 指定の Swift Package Manager では取り込めない可能性が高い。** ローカルパッケージとしてフォルダごと置くか、必要な部分だけコピーする。
- コピーするなら **MIT の著作権表示とライセンス文を残す**(`LICENSE`)。`docs/asset_list.md` に出典・条件・確認日を記録する。
- 同梱のフォント・アイコン素材の条件は、コードとは別。使う前に公式で確認する。
- 部品の見た目・挙動が「動きを減らす」設定やアクセシビリティの要件(タップ領域 44pt 以上など)を満たすかは、取り込み後に実機で確認する。

## 使い方(段階)
1. **最小**: 設計の参考にする。`docs/design/` の文書(動き、動きを減らす設定、モバイルの文字、状態)を読み、自分のトークン表(`philosophy/design_principles.md`)に反映する。コードは取り込まない。
2. **トークンだけ**: 生成されたトークン(`Theme/Generated/`)の構造を真似て、自分のアプリ用の型つきトークンを作る。**テーマ名・色は、アプリごとに作り直す**(既製テーマの流用は避ける)。
3. **一部の部品**: 足りない部品だけコピーする。使う部品を最初に決め、増やさない。
4. **丸ごと**: 実験段階のため、オーナーが明示した時だけ。バージョンを固定し、更新は手動で。

## 守ること(フォーマットとの整合)
- フォントは `philosophy/fonts.md` の固定リストのみ。テーマのフォント指定を、固定リストに置き換える。
- Era / Rule / Voice の縛りを、トークンの選択(色・角丸・余白・文字)に反映する。
- 既製テーマ名・色をそのまま使わない。審査メモや説明文で「Astryx 製」と宣伝しない(実質の価値は体験で示す)。
- 取り込んだコードも、`2_development.md` と pre-commit の対象。
