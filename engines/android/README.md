# Android ネイティブ(初版)

初版を整備済み(2026-11-06)。技術の標準方針は `CLAUDE.part.md`。
標準(Kotlin + Jetpack Compose、UI 層とデータ層、ViewModel + StateFlow、Room / DataStore の使い分け、48dp のタップ領域、アニメーション倍率の取得)は、公式(developer.android.com)で確認済み(2026-11-06。`workflow/android_guide.md`)。
未確認: 「アニメーションを削除」のトグルがアニメーション倍率を 0 にするか(実機で確認)、コントラスト比の数値。
未整備: 書き出し・署名の詳細手順、Compose 固有の実装パターン、フォントや起動アニメーションの実装例。最初に作る時に、公式を確認して整備する。
