# 機能詳細

## 1. フォルダ構造カスタマイズ

ユーザーは、コピー先のフォルダ構造を柔軟に定義できます。

- **利用可能な情報**: 以下の情報をフォルダ名や階層に利用可能です。
    - 撮影年月日 (年、月、日、時、分、秒)
    - 使用カメラメーカー名
    - 使用カメラモデル名
    - レンズ情報 (モデル名、焦点距離など)
    - ファイル種別 (動画, 写真, RAWなど)
    - GPS情報 (国、都道府県、市町村など、取得可能な場合)
    - 任意の固定文字列
    - 連番
- **設定方法**: GUI上で、利用可能な情報をドラッグ＆ドロップまたは選択形式で組み合わせ、プレビューしながらフォルダ構造パターンを作成します。CUIでは、設定ファイルに特定の書式で記述します。
- **例**:
    - `写真/{撮影年}/{撮影月}/{撮影日}` -> `写真/2023/10/27`
    - `動画/{カメラモデル}/{撮影年}-{撮影月}` -> `動画/SONY ILCE-7M4/2023-10`
    - `旅行/{撮影年}/{GPS国}/{GPS都道府県}` -> `旅行/2024/Japan/Tokyo`

## 2. ファイルハッシュによる重複検知

コピー先に既に同一ファイルが存在するかどうかを、ファイルハッシュ（SHA-256など）を比較することで検知します。

- **動作**: コピー処理時、コピー元ファイルのハッシュ値と、コピー先候補に同名ファイルが存在する場合はそのハッシュ値を計算・比較します。
- **オプション**:
    - **スキップ**: 重複ファイルをコピーせずスキップします。
    - **上書き**: 重複ファイルを上書きします。（ファイル名変更機能と併用しない場合は注意）
    - **名前を変更して保存**: 後述のファイル名変更機能に従い、新しい名前で保存します。
    - **ユーザーに確認**: GUIの場合、重複時にユーザーに動作を選択させます。
- **ハッシュキャッシュ**: パフォーマンス向上のため、一度計算したファイルのハッシュ値をキャッシュする仕組みを検討します（ファイルパス、最終更新日時、ファイルサイズをキーとするなど）。

## 3. ファイル名変更機能

コピー時に、ファイル名を指定のルールに基づいて変更します。

- **目的**: カメラ内で連番管理されるファイル名（例: `DSC00001.JPG`）が、異なるメディアや撮影日で重複することによる上書き事故を防止します。また、ファイル名から内容を推測しやすくします。
- **利用可能な情報**: フォルダ構造カスタマイズと同様の情報（撮影日時、カメラモデルなど）に加え、元のファイル名、連番（処理単位または日単位など）を利用できます。
- **設定方法**: GUI上で、利用可能な情報を組み合わせて命名規則パターンを作成します。CUIでは設定ファイルに記述します。
- **例**:
    - `元のファイル名` -> `DSC00001.JPG`
    - `{撮影年月日}_{時分秒}_{連番3桁}` -> `20231027_153000_001.MP4`
    - `{カメラモデル}_{撮影年月日}_{元のファイル名}` -> `ILCE-7M4_20231027_DSC00001.JPG`
- **衝突回避**: 生成したファイル名がコピー先に既に存在する場合、末尾に連番や識別子を付与して衝突を回避します (例: `filename_1.ext`, `filename_2.ext`)。

## 4. メタデータなど付随ファイルの同時コピー

メインの動画・写真ファイルに付随する関連ファイルを自動的に検出し、同じ整理ルール（または指定されたルール）でコピーします。

- **対象ファイル (例)**:
    - サイドカーファイル: `.XMP` (Adobeメタデータ), `.AAE` (iOS編集情報)
    - サムネイルファイル: `.THM`
    - RAW+JPEGの場合のペアファイル
    - 動画の音声ファイル (例: 特定のカメラ機種の仕様)
    - GPSログファイル (GPXなど、同名またはタイムスタンプで紐づけ)
- **検出方法**: メインファイルと同じ名前（拡張子除く）のファイル、または特定の命名規則を持つファイルを関連ファイルとして扱います。
- **設定**: 関連ファイルの拡張子や命名規則をユーザーが設定できるようにします。

## 5. CUIによる自動化機能

GUIで設定した内容（プリセット）を利用して、CUIからコマンドラインで処理を実行できます。

- **プリセット管理**: GUIで作成したフォルダ構造、ファイル命名規則、コピー先、重複処理などの設定を「プリセット」として名前を付けて保存・管理できます。
- **CUIコマンド例**:
    ```bash
    video_copy_tool --preset "MyVacationPreset" --source "/Volumes/SD_CARD/DCIM" --destination "/Users/username/Pictures/Vacations"
    video_copy_tool --config "path/to/custom_config.json" --source "D:\CameraUploads" --destination "N:\PhotosArchive"
    video_copy_tool --scan-only --source "/media/camera" --preset "BackupPreset"  # スキャンのみ実行
    video_copy_tool --list-presets  # 利用可能なプリセット一覧表示
    ```
- **オプション**: 
    - `--source <path>`: コピー元のフォルダを指定します。
    - `--destination <path>`: コピー先のルートフォルダを指定します。
    - `--preset <name>`: 保存されたプリセット名を指定します。
    - `--config <filepath>`: プリセットファイル（JSON/YAML）のパスを直接指定します。
    - `--dry-run`: 実際のコピーは行わず、処理内容のプレビューを表示します。
    - `--scan-only`: ファイルスキャンのみ実行し、コピー予定の詳細情報を表示します。
    - `--log-level <level>`: ログの詳細度を指定します (debug, info, warn, error)。
    - `--log-file <filepath>`: ログの出力先ファイルを指定します。
    - `--progress`: 進捗バーを表示します（デフォルトで有効）。
    - `--no-progress`: 進捗バーを非表示にします。
    - `--list-presets`: 利用可能なプリセットの一覧を表示します。
    - `--validate-config`: 設定ファイルの妥当性をチェックします。
    - `--yes`: 確認プロンプトを全て「はい」として自動応答します。
    - `--quiet`: 最小限の出力のみ表示します（エラー時を除く）。
    - `--help`: ヘルプメッセージを表示します。
    - `--version`: バージョン情報を表示します。
- **出力とログ**: 
    - **標準出力**: 処理の進捗、結果サマリー、重要な情報を表示します。
    - **標準エラー出力**: エラーメッセージ、警告、診断情報を表示します。
    - **ログファイル**: 詳細なログ（実行したアクション、処理したファイルリスト、エラー詳細など）を指定ファイルに出力します。
    - **進捗表示**: ファイル数、処理済み容量、残り時間予測などをリアルタイム表示します。
- **終了コード**: 処理結果に応じて適切な終了コードを返却し、スクリプトでの後続処理を容易にします。
    - `0`: 正常終了（全てのファイルが正常に処理された）
    - `1`: 一般的なエラー（設定エラー、権限エラーなど）
    - `2`: コマンドライン引数エラー
    - `3`: 一部ファイルでエラーが発生したが、他は正常処理
    - `4`: 重複ファイル検出による処理スキップが発生
    - `64`: 設定ファイルの形式エラー
    - `65`: 入力ファイル/フォルダが見つからない
    - `66`: 出力先への書き込み権限なし

## 6. ケーブル接続デバイス対応

iPhone、iPad、Androidデバイス、デジタルカメラなどをUSBやThunderboltケーブルで直接PC/Macに接続して、コピー元として利用できます。

### 6.1 対応デバイス

- **iOS デバイス (iPhone/iPad)**:
    - iOS 13.0以降のデバイス
    - Lightning - USBケーブルまたはUSB-C - USBケーブル経由
    - 写真アプリ内のメディアライブラリへのアクセス
    - DCIM、Photos、Recents、Albums等のフォルダ構造に対応
- **Android デバイス**:
    - Android 6.0以降でMTP (Media Transfer Protocol) 対応デバイス
    - USB-C、micro-USB等のケーブル経由
    - 内部ストレージおよびSDカード内のDCIMフォルダへのアクセス
- **デジタルカメラ**:
    - Mass Storage Class (MSC) 対応カメラ
    - PTP (Picture Transfer Protocol) 対応カメラ
    - CF、SD、microSDカード等のメモリカード経由でのアクセス

### 6.2 デバイス検出と認識

- **自動検出**: 
    - システムに接続されたMTP、PTP、MSCデバイスを自動的に検出
    - デバイス名、モデル名、シリアル番号等の基本情報を取得
    - 利用可能なストレージ容量と使用済み容量を表示
- **デバイス一覧表示**:
    - GUIでは接続されたデバイスをアイコン付きで一覧表示
    - デバイスタイプ（iPhone、Android、Camera等）を視覚的に区別
    - 接続状態（利用可能、認証待ち、エラー等）を表示
- **権限要求処理**:
    - iOS: iPhoneで「このコンピューターを信頼」確認への対応
    - Android: ファイル転送モード（MTP）選択のガイダンス表示
    - macOS: システム環境設定でのアクセス許可確認のガイダンス

### 6.3 フォルダ構造の認識

各デバイスタイプに応じた標準的なフォルダ構造を認識し、メディアファイルを効率的に検出します：

- **iOS デバイス**:
    ```
    /DCIM/
      100APPLE/  # Camera Roll
      101APPLE/  # 追加の写真
      ...
    /PhotoData/  # Live Photos等の関連データ
    ```
- **Android デバイス**:
    ```
    /DCIM/Camera/     # 標準カメラアプリ
    /DCIM/100MEDIA/   # 一部機種
    /Pictures/        # スクリーンショット等
    /Movies/          # 動画ファイル
    /Download/        # ダウンロードファイル
    ```
- **デジタルカメラ**:
    ```
    /DCIM/100MSDCF/   # 標準CF規格
    /DCIM/100CANON/   # Canon
    /DCIM/100NIKON/   # Nikon
    /PRIVATE/         # メーカー固有データ
    ```

### 6.4 接続安定性とエラーハンドリング

- **接続監視**: 
    - コピー処理中のデバイス切断を検出
    - 一時的な接続不良時の自動再試行機能（最大3回）
    - 処理中断時の状況保存と復旧機能
- **エラー対応**:
    - デバイス固有のエラー（容量不足、ファイルロック等）への対応
    - わかりやすいエラーメッセージとトラブルシューティングガイド
    - ログファイルでの詳細エラー情報記録
- **パフォーマンス最適化**:
    - USB転送速度に応じた並列処理数の調整
    - メタデータ取得の効率化（デバイス上でのEXIF読取り等）
    - 大容量ファイル転送時のプログレス表示

### 6.5 CUIでの利用

```bash
# 接続デバイス一覧表示
video_copy_tool --list-devices

# 特定デバイスを指定してコピー
video_copy_tool --device "iPhone (John's)" --destination "/Users/john/Pictures/iPhone_Photos"

# デバイスIDを指定
video_copy_tool --device-id "com.apple.iPhone.12345" --preset "iPhonePreset"

# 複数デバイスの一括処理
video_copy_tool --device "*" --destination "/Backup/AllDevices/{device_name}/{date}"
```

### 6.6 セキュリティとプライバシー

- **アクセス制御**: 
    - デバイス側での認証・許可が必要なアクセスのみ実行
    - ユーザーが明示的に選択したフォルダのみスキャン
- **データ保護**: 
    - コピー元ファイルの変更は一切行わない（読み取り専用アクセス）
    - 一時ファイルやキャッシュの適切な削除
- **プライバシー配慮**: 
    - システムフォルダや非公開フォルダへのアクセス禁止
    - メタデータ取得時の個人情報保護（GPS位置情報の扱い等） 

## 7. スクリーンショット除外機能

iPhoneやAndroidデバイスからの写真コピー時に、スクリーンショットファイルを自動的に除外する機能です。

### 7.1 スクリーンショット判定方法

スクリーンショットの判定は以下の複数の方法を組み合わせて行います：

#### 7.1.1 ファイル名パターンによる判定
- **iOSスクリーンショット**: `IMG_XXXX.PNG`形式のファイル
- **Androidスクリーンショット**: `Screenshot_*.png`形式のファイル
- **日本語環境**: `スクリーンショット_*.png`形式のファイル
- **カスタムパターン**: ユーザーが独自に定義したパターン

#### 7.1.2 ファイルパスによる判定
- **Android**: `/Pictures/Screenshots/`フォルダ内のファイル
- **iOS**: `/Pictures/`フォルダ内のPNGファイル（DCIMフォルダ外）
- **共通**: スクリーンショット専用フォルダ内のファイル

#### 7.1.3 メタデータによる判定
- **EXIFデータ**: ImageDescriptionやSoftwareフィールドに「Screenshot」が含まれる
- **画像解像度**: デバイスの画面解像度と一致するPNGファイル
- **デバイス特有情報**: iOS/Android特有のメタデータパターン

### 7.2 設定方法

#### 7.2.1 プリセット設定での有効化
```json
{
  "fileFilters": {
    "enableFilters": true,
    "excludeScreenshots": true,
    "screenshotDetection": {
      "enableFilenamePattern": true,
      "enablePathPattern": true,
      "enableMetadataPattern": true,
      "enableResolutionDetection": true,
      "customPatterns": [
        "^screenshot.*\\.png$",
        "^スクリーンショット.*\\.png$"
      ]
    }
  }
}
```

#### 7.2.2 CUIでの使用
```bash
# スクリーンショットを除外してiPhoneからコピー
video_copy_tool --source "/Volumes/iPhone/DCIM" \
                --destination "/Users/user/Pictures/iPhone" \
                --exclude-screenshots \
                --source-device iOS

# 詳細な統計情報付きで実行
video_copy_tool --source "/path/to/photos" \
                --destination "/path/to/destination" \
                --exclude-screenshots \
                --show-filter-stats

# 画像のみでスクリーンショット除外
video_copy_tool --source "/path/to/photos" \
                --destination "/path/to/destination" \
                --include-media-types image \
                --exclude-screenshots
```

### 7.3 判定精度の向上

#### 7.3.1 デバイス特有の設定
デバイスタイプを指定することで、より精度の高い判定が可能です：

```bash
# iOSデバイス用設定
video_copy_tool --source-device iOS --exclude-screenshots

# Androidデバイス用設定  
video_copy_tool --source-device Android --exclude-screenshots
```

#### 7.3.2 カスタムパターンの追加
特殊な命名規則を持つスクリーンショットに対応するため、カスタムパターンを設定できます：

```json
{
  "screenshotDetection": {
    "customPatterns": [
      "^capture_\\d{8}_\\d{6}\\.png$",
      "^screen_record.*\\.mp4$"
    ]
  }
}
```

### 7.4 統計とログ

#### 7.4.1 フィルタ統計の表示
```bash
video_copy_tool --exclude-screenshots --show-filter-stats
```

出力例：
```
=== フィルタ統計 ===
総ファイル数: 1,245
処理対象ファイル数: 1,156
除外ファイル数: 89
処理率: 92.9%

=== 除外理由別詳細 ===
  スクリーンショット: 89ファイル
```

#### 7.4.2 ログ出力
```
INFO - Excluded screenshot: IMG_0123.PNG
INFO - Excluded screenshot: Screenshot_2024-01-15-10-30-25.png
INFO - Filter results: 1156/1245 files included (92.9%)
INFO - Excluded files breakdown: screenshots: 89
```

### 7.5 高度な機能

#### 7.5.1 選択的フィルタ有効化
特定の判定方法のみを有効にすることができます：

```json
{
  "screenshotDetection": {
    "enableFilenamePattern": true,
    "enablePathPattern": false,
    "enableMetadataPattern": true,
    "enableResolutionDetection": false
  }
}
```

#### 7.5.2 ファイルサイズフィルタとの組み合わせ
```bash
# 1MB以上のファイルのみを対象とし、スクリーンショットは除外
video_copy_tool --min-file-size 1048576 --exclude-screenshots
```

### 7.6 対応デバイスと形式

#### 7.6.1 対応デバイス
- **iOS デバイス**: iPhone、iPad（iOS 13.0以降）
- **Android デバイス**: Android 6.0以降のMTP対応デバイス
- **その他**: 汎用的なパターンマッチングによる対応

#### 7.6.2 対応ファイル形式
- **主要形式**: PNG、JPG/JPEG
- **拡張対応**: HEIC、WebP（設定により）

### 7.7 トラブルシューティング

#### 7.7.1 誤判定の対処
スクリーンショットではないファイルが除外される場合：

1. カスタムパターンを調整
2. 特定の判定方法を無効化
3. ファイル名やフォルダ構造を確認

#### 7.7.2 検出漏れの対処
スクリーンショットが除外されない場合：

1. デバイスタイプを正しく指定
2. カスタムパターンを追加
3. メタデータ判定を有効化

// ... existing code ... 