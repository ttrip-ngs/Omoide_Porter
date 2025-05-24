# データ構造

## 1. 設定ファイル（プリセット）

アプリケーションの設定やユーザーが作成したプリセットは、JSONまたはYAML形式のファイルで管理します。これにより、可読性が高く、手動での編集も比較的容易になります。

以下は設定ファイルの構造例です（JSON形式）。

```json
{
  "version": "1.0",
  "presets": [
    {
      "name": "MyVacationPreset",
      "source": null,
      "destination": "/Users/username/Pictures/Vacations",
      "folderStructure": {
        "levels": [
          {"type": "literal", "value": "Events"},
          {"type": "metadata", "field": "year"},
          {"type": "metadata", "field": "month", "format": "%02d"},
          {"type": "metadata", "field": "day", "format": "%02d"}
        ],
        "separator": "/"
      },
      "fileNamePattern": {
        "components": [
          {"type": "metadata", "field": "datetime", "format": "YYYYMMDD_HHMMSS"},
          {"type": "literal", "value": "_"},
          {"type": "original_filename", "includeExtension": false},
          {"type": "original_extension"}
        ],
        "conflictResolution": {
          "type": "sequence",
          "digits": 3,
          "position": "before_extension"
        }
      },
      "duplicateHandling": "rename",
      "includeAssociatedFiles": true,
      "associatedFileRules": {
        "sameBaseName": ["xmp", "thm", "aae"],
        "videoToImage": ["jpg", "jpeg"],
        "customPatterns": []
      },
      "fileFilters": {
        "enableFilters": true,
        "includeMediaTypes": ["image", "video", "raw"],
        "excludeMediaTypes": [],
        "excludeScreenshots": true,
        "screenshotDetection": {
          "enableFilenamePattern": true,
          "enablePathPattern": true,
          "enableMetadataPattern": true,
          "enableResolutionDetection": true,
          "customPatterns": [
            "^img_\\d{4}\\.png$",
            "^screenshot.*\\.png$"
          ]
        },
        "excludeByFilename": [],
        "excludeByPath": [],
        "minFileSize": 1024,
        "maxFileSize": null,
        "includeExtensions": [],
        "excludeExtensions": []
      },
      "logLevel": "info"
    },
    {
      "name": "WorkBackup",
      "destination": "N:/Backup/WorkFiles",
      "folderStructure": {
        "levels": [
          {"type": "metadata", "field": "year"},
          {"type": "literal", "value": "-"},
          {"type": "metadata", "field": "month", "format": "%02d"}
        ],
        "separator": "/"
      },
      "fileNamePattern": {
        "components": [
          {"type": "original_filename"}
        ]
      },
      "duplicateHandling": "skip",
      "includeAssociatedFiles": false,
      "fileFilters": {
        "enableFilters": false,
        "excludeScreenshots": false
      },
      "logLevel": "warn"
    },
    {
      "name": "iPhonePhotosNoScreenshots",
      "source": null,
      "destination": "/Users/username/Pictures/iPhone",
      "folderStructure": {
        "levels": [
          {"type": "metadata", "field": "year"},
          {"type": "metadata", "field": "month", "format": "%02d"}
        ],
        "separator": "/"
      },
      "fileNamePattern": {
        "components": [
          {"type": "metadata", "field": "datetime", "format": "YYYYMMDD_HHMMSS"},
          {"type": "literal", "value": "_"},
          {"type": "original_filename", "includeExtension": false},
          {"type": "original_extension"}
        ]
      },
      "duplicateHandling": "rename",
      "includeAssociatedFiles": true,
      "associatedFileRules": {
        "sameBaseName": ["aae"],
        "videoToImage": ["jpg", "jpeg"],
        "customPatterns": []
      },
      "fileFilters": {
        "enableFilters": true,
        "includeMediaTypes": ["image", "video"],
        "excludeScreenshots": true,
        "screenshotDetection": {
          "enableFilenamePattern": true,
          "enablePathPattern": true,
          "enableMetadataPattern": true,
          "enableResolutionDetection": true,
          "customPatterns": []
        }
      },
      "logLevel": "info"
    }
  ],
  "globalSettings": {
    "defaultSource": "/Volumes/UNTITLED",
    "defaultDestination": "/Users/username/Desktop/CopiedFiles",
    "hashAlgorithm": "sha256",
    "cacheHashes": true,
    "maxConcurrentOperations": 4,
    "bufferSize": 65536,
    "deviceSettings": {
      "autoDetectDevices": true,
      "enableDeviceNotifications": true,
      "connectionTimeout": 30,
      "transferRetryCount": 3,
      "maxDeviceConnections": 5
    }
  },
  "deviceProfiles": [
    {
      "deviceId": "com.apple.iPhone.*",
      "deviceType": "iOS",
      "displayName": "iPhone",
      "icon": "phone",
      "defaultPaths": ["/DCIM", "/PhotoData"],
      "supportedFormats": ["jpg", "jpeg", "heic", "mov", "mp4", "m4v"],
      "requiresAuthentication": true,
      "transferProtocol": "AFC"
    },
    {
      "deviceId": "android.*",
      "deviceType": "Android",
      "displayName": "Android Device",
      "icon": "phone-android",
      "defaultPaths": ["/DCIM/Camera", "/Pictures", "/Movies"],
      "supportedFormats": ["jpg", "jpeg", "png", "mp4", "3gp", "webm"],
      "requiresAuthentication": false,
      "transferProtocol": "MTP"
    },
    {
      "deviceId": "camera.*",
      "deviceType": "Camera",
      "displayName": "Digital Camera",
      "icon": "camera",
      "defaultPaths": ["/DCIM"],
      "supportedFormats": ["jpg", "jpeg", "raw", "cr2", "nef", "arw", "mp4", "mov"],
      "requiresAuthentication": false,
      "transferProtocol": "PTP"
    }
  ]
}
```

**主なフィールド解説**: 

- `presets`: プリセットの配列。
    - `name`: プリセット名。
    - `source`: （オプション）デフォルトのコピー元パス。
    - `destination`: デフォルトのコピー先パス。
    - `folderStructure`: フォルダ構造の定義。
        - `levels`: 階層レベルの配列。各要素が1つのフォルダ名を構成。
            - `type`: `literal` (固定文字列), `metadata` (撮影情報など), `sequence` (連番)
            - `field`: `metadata`タイプの場合の取得フィールド (例: `year`, `month`, `cameraModel`)
            - `format`: （オプション）フォーマット指定 (例: `%02d`で2桁0埋め、`YYYYMMDD`で日付形式)
            - `value`: `literal`タイプの場合の固定値
        - `separator`: フォルダ区切り文字（通常は"/"、Windowsでは自動変換）
    - `fileNamePattern`: ファイル名の命名規則。
        - `components`: ファイル名を構成する要素の配列。
            - `type`: `literal`, `metadata`, `original_filename`, `original_extension`, `sequence`など
            - `field`: `metadata`タイプの場合のフィールド名
            - `format`: フォーマット指定
            - `includeExtension`: `original_filename`の場合、拡張子を含むかどうか
        - `conflictResolution`: ファイル名衝突時の解決方法
            - `type`: `sequence` (連番), `timestamp` (タイムスタンプ追加)
            - `digits`: 連番の桁数
            - `position`: 挿入位置 (`before_extension`, `after_name`)
    - `duplicateHandling`: 重複時の処理 (`skip`, `overwrite`, `rename`, `ask`)。
    - `includeAssociatedFiles`: 関連ファイルをコピーするかどうか (boolean)。
    - `associatedFileRules`: 関連ファイルの認識ルール。
        - `sameBaseName`: 同じベース名（拡張子を除く）のファイルとして認識する拡張子リスト
        - `videoToImage`: 動画ファイルに対応する静止画ファイル拡張子リスト
        - `customPatterns`: カスタムパターン（将来の拡張用）
    - `fileFilters`: ファイルフィルタの設定。
        - `enableFilters`: フィルタを有効にするか
        - `includeMediaTypes`: 含むメディアタイプのリスト
        - `excludeMediaTypes`: 除外メディアタイプのリスト
        - `excludeScreenshots`: スクリーンショットを除外するか
        - `screenshotDetection`: スクリーンショット検出の設定
            - `enableFilenamePattern`: ファイル名パターンに基づく検出を有効にするか
            - `enablePathPattern`: パスパターンに基づく検出を有効にするか
            - `enableMetadataPattern`: メタデータパターンに基づく検出を有効にするか
            - `enableResolutionDetection`: 解像度に基づく検出を有効にするか
            - `customPatterns`: カスタムパターンのリスト
        - `excludeByFilename`: ファイル名に基づく除外ルール
        - `excludeByPath`: パスに基づく除外ルール
        - `minFileSize`: 最小ファイルサイズ（バイト）
        - `maxFileSize`: 最大ファイルサイズ（バイト）
        - `includeExtensions`: 含む拡張子のリスト
        - `excludeExtensions`: 除外拡張子のリスト
    - `logLevel`: このプリセット実行時のログレベル。
- `globalSettings`: アプリケーション全体の共通設定。
    - `defaultSource`, `defaultDestination`: デフォルトのコピー元・先。
    - `hashAlgorithm`: 使用するハッシュアルゴリズム。
    - `cacheHashes`: ハッシュキャッシュを有効にするか。
    - `maxConcurrentOperations`: 並列処理数の上限。
    - `bufferSize`: ファイルI/Oのバッファサイズ。
- `deviceSettings`: デバイス接続に関するグローバル設定
    - `autoDetectDevices`: デバイスの自動検出を有効にするか
    - `enableDeviceNotifications`: デバイス接続/切断通知を有効にするか
    - `connectionTimeout`: デバイス接続タイムアウト時間（秒）
    - `transferRetryCount`: 転送失敗時の再試行回数
    - `maxDeviceConnections`: 同時接続可能デバイス数
- `deviceProfiles`: デバイスタイプ別の設定プロファイル
    - `deviceId`: デバイスID識別パターン（正規表現）
    - `deviceType`: デバイスカテゴリ（iOS, Android, Camera等）
    - `displayName`: UI表示用の名前
    - `icon`: アイコン識別子
    - `defaultPaths`: デフォルトでスキャンするパス
    - `supportedFormats`: 対応ファイル形式
    - `requiresAuthentication`: 認証が必要かどうか
    - `transferProtocol`: 使用する転送プロトコル

## 2. 内部で扱うファイル情報

アプリケーション内部でファイルを処理する際には、以下のような情報を持つオブジェクトまたは構造体として扱います。

```python
# Python例（疑似コード）
class DeviceInfo:
    # デバイス基本情報
    deviceId: str          # システムレベルのデバイスID
    deviceType: str        # iOS, Android, Camera等
    displayName: str       # UI表示用の名前
    manufacturer: str      # メーカー名
    model: str            # モデル名
    serialNumber: str     # シリアル番号
    
    # 接続情報
    protocol: str         # AFC, MTP, PTP等
    connectionPath: str   # システムでのマウントパス
    isAuthenticated: bool # 認証状態
    connectionStatus: str # connected, disconnected, authenticating, error
    
    # ストレージ情報
    totalCapacity: int    # 総容量（バイト）
    freeSpace: int        # 空き容量（バイト）
    availablePaths: List[str]  # アクセス可能なパス一覧
    
    # 転送情報
    transferSpeed: float  # 現在の転送速度（MB/s）
    lastConnected: datetime  # 最終接続時刻

class FileInfo:
    # 元ファイル情報
    originalPath: str
    originalFileName: str
    originalBaseName: str  # 拡張子を除いたファイル名
    originalExtension: str
    size: int
    lastModified: datetime
    
    # ソース情報
    sourceType: str  # "folder", "device"
    sourceDevice: DeviceInfo  # デバイスからの場合のみ設定
    
    # メディア情報
    mediaType: str  # video, image, audio, document, unknown
    mimeType: str
    
    # メタデータ
    metadata: dict  # 抽出されたメタデータのキーバリューペア
    # 標準的なメタデータフィールド:
    #   - dateTimeOriginal: datetime
    #   - cameraMake: str
    #   - cameraModel: str
    #   - lensModel: str
    #   - focalLength: float
    #   - gpsLatitude: float
    #   - gpsLongitude: float
    #   - gpsLocationName: str  # 逆ジオコーディング結果
    #   - orientation: int
    #   - width: int
    #   - height: int
    #   - duration: float  # 動画の場合
    
    # 処理結果
    hash: str  # 計算後のハッシュ値
    targetPath: str  # 計算されたコピー先のフルパス
    targetFileName: str  # 計算されたコピー後のファイル名
    status: str  # pending, copying, copied, skipped, error, duplicate
    errorMessage: str  # エラー時のメッセージ
    
    # 関連ファイル
    associatedFiles: List[FileInfo]  # 関連ファイルのリスト
    isAssociatedFile: bool  # このファイル自体が関連ファイルかどうか
    parentFile: FileInfo  # 関連ファイルの場合、親ファイルの参照
```

**主なフィールド解説**:

**DeviceInfo**:
- `deviceId`: システムが認識するデバイスの一意識別子
- `deviceType`: デバイスカテゴリ（iOS、Android、Camera等）
- `displayName`: ユーザーに表示するデバイス名
- `manufacturer`: デバイスメーカー（Apple、Samsung等）
- `model`: デバイスモデル名（iPhone 15 Pro、Galaxy S24等）
- `serialNumber`: デバイスのシリアル番号
- `protocol`: 通信プロトコル（AFC、MTP、PTP等）
- `connectionPath`: システム内でのマウントパスやデバイスパス
- `isAuthenticated`: デバイスとの認証が完了しているか
- `connectionStatus`: 現在の接続状態
- `totalCapacity`: デバイスの総ストレージ容量
- `freeSpace`: デバイスの空き容量
- `availablePaths`: アクセス可能なフォルダパス一覧
- `transferSpeed`: 現在の転送速度
- `lastConnected`: 最後に接続された日時

**FileInfo**:
- `originalPath`: コピー元のフルパス
- `originalFileName`: 元のファイル名（拡張子込み）
- `originalBaseName`: 拡張子を除いた元のファイル名
- `originalExtension`: 元の拡張子（ピリオドを含む、例: ".jpg"）
- `size`: ファイルサイズ（バイト）
- `lastModified`: 最終更新日時
- `sourceType`: ソースの種類（フォルダまたはデバイス）
- `sourceDevice`: デバイスからの場合のデバイス情報
- `mediaType`: 推測されるメディア種別
- `mimeType`: MIMEタイプ
- `metadata`: EXIFなどの抽出されたメタデータ
- `hash`: ファイルハッシュ値（重複検知用）
- `targetPath`: 設定に基づいて計算されたコピー先フルパス
- `targetFileName`: 設定に基づいて計算されたコピー後ファイル名
- `status`: 処理の状況
- `associatedFiles`: このファイルに関連する他のファイルのリスト
- `isAssociatedFile`: このファイルが他のファイルの関連ファイルかどうか
- `parentFile`: 関連ファイルの場合、メインファイルへの参照 