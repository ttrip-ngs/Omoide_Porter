# フィルター拡張ガイド

## 概要

このドキュメントでは、動画・写真コピーツールのフィルターシステムを拡張する方法について説明します。新しいフィルタークラスの実装から、設定ファイルでの使用まで、詳細な手順を提供します。

## アーキテクチャ概要

フィルターシステムは以下のコンポーネントで構成されています：

- **BaseFilter**: 全フィルターの基底クラス
- **FilterResult**: フィルター判定結果を表すクラス
- **FilterChain**: 複数のフィルターを順次実行するクラス
- **FilterRegistry**: フィルタープラグインの登録・管理クラス

## 新しいフィルターの作成手順

### 1. BaseFilterクラスを継承

```python
from ..filter_base import BaseFilter, FilterResult
from ..file_info import FileInfo

class MyCustomFilter(BaseFilter):
    """カスタムフィルターの例"""
    
    def __init__(self, config: Dict[str, Any], filter_id: str):
        super().__init__(config, filter_id)
        # 設定から必要なパラメータを取得
        self.my_parameter = config.get("myParameter", "default_value")
    
    def check_file(self, file_info: FileInfo) -> FilterResult:
        """ファイルのフィルタリング判定を実装"""
        # フィルタリングロジックを実装
        if self._should_exclude_file(file_info):
            return FilterResult(
                include=False,
                reason="Custom exclusion reason",
                metadata={"custom_data": "some_value"}
            )
        
        return FilterResult(include=True)
    
    def get_filter_name(self) -> str:
        return "My Custom Filter"
    
    def get_filter_description(self) -> str:
        return f"Custom filter with parameter: {self.my_parameter}"
```

### 2. 必須メソッドの実装

#### check_file(self, file_info: FileInfo) -> FilterResult
- **目的**: ファイルがフィルター条件を満たすかどうかを判定
- **戻り値**: `FilterResult`オブジェクト
  - `include`: ファイルを含める場合`True`、除外する場合`False`
  - `reason`: 除外理由（除外時のみ）
  - `metadata`: フィルター固有の追加情報

#### get_filter_name(self) -> str
フィルターの名前を返します。

#### get_filter_description(self) -> str
フィルターの説明を返します。設定内容を含めることを推奨します。

### 3. オプションメソッドの実装

#### get_config_schema(self) -> Dict[str, Any]
設定のJSONスキーマを返します。設定の妥当性チェックやUI生成に使用されます。

```python
def get_config_schema(self) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "myParameter": {
                "type": "string",
                "default": "default_value",
                "description": "カスタムパラメータの説明"
            },
            "enabled": {"type": "boolean", "default": True},
            "priority": {"type": "integer", "default": 100}
        }
    }
```

## 標準フィルターの例

### MediaTypeFilter
メディアタイプ（画像、動画、音声など）によるフィルタリング

```json
{
  "media_type": {
    "enabled": true,
    "priority": 10,
    "includeTypes": ["image", "video"],
    "excludeTypes": ["audio"]
  }
}
```

### ScreenshotFilter
スクリーンショットファイルの除外

```json
{
  "screenshot": {
    "enabled": true,
    "priority": 50,
    "excludeScreenshots": true,
    "deviceType": "iOS",
    "detection": {
      "enableFilenamePattern": true,
      "enablePathPattern": true,
      "enableMetadataPattern": true,
      "customPatterns": ["^capture.*\\.png$"]
    }
  }
}
```

### DateRangeFilter
日付範囲によるフィルタリング

```json
{
  "date_range": {
    "enabled": true,
    "priority": 30,
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "useMetadataDate": true,
    "dateField": "datetime"
  }
}
```

## フィルターの登録

### 1. 手動登録
```python
from src.core.filter_base import filter_registry
from my_filters import MyCustomFilter

# フィルターを登録
filter_registry.register_filter("my_custom", MyCustomFilter)
```

### 2. モジュール内での自動登録
```python
# src/core/filters/my_custom_filter.py
from ..filter_base import filter_registry

class MyCustomFilter(BaseFilter):
    # ... 実装 ...

# モジュール読み込み時に自動登録
filter_registry.register_filter("my_custom", MyCustomFilter)
```

## 設定ファイルでの使用

```json
{
  "name": "MyPreset",
  "filters": {
    "my_custom": {
      "enabled": true,
      "priority": 75,
      "myParameter": "custom_value"
    },
    "media_type": {
      "enabled": true,
      "priority": 10,
      "includeTypes": ["image"]
    }
  }
}
```

## フィルター実行順序

フィルターは`priority`値の小さい順に実行されます：

1. `priority: 10` - MediaTypeFilter
2. `priority: 30` - DateRangeFilter  
3. `priority: 50` - ScreenshotFilter
4. `priority: 75` - MyCustomFilter

## デバッグとテスト

### ログ出力の活用
```python
import logging
logger = logging.getLogger(__name__)

def check_file(self, file_info: FileInfo) -> FilterResult:
    logger.debug(f"Checking file: {file_info.original_filename}")
    # フィルタリングロジック
    logger.info(f"File {file_info.original_filename} result: {result}")
```

### テストケースの作成
```python
import unittest
from src.core.file_info import FileInfo
from my_filters import MyCustomFilter

class TestMyCustomFilter(unittest.TestCase):
    def test_filter_logic(self):
        config = {"myParameter": "test_value"}
        filter_instance = MyCustomFilter(config, "test")
        
        file_info = FileInfo("/path/to/test.jpg")
        result = filter_instance.check_file(file_info)
        
        self.assertTrue(result.include)
```

## 実装のベストプラクティス

### 1. パフォーマンス考慮
- 重い処理（ファイルI/O、メタデータ解析）は最小限に
- 早期リターンを活用
- 必要に応じてキャッシュを実装

### 2. エラーハンドリング
```python
def check_file(self, file_info: FileInfo) -> FilterResult:
    try:
        # フィルタリングロジック
        pass
    except Exception as e:
        logger.error(f"Filter error: {e}")
        return FilterResult(include=True)  # エラー時はデフォルトで含める
```

### 3. 設定の妥当性チェック
```python
def validate_config(self) -> Tuple[bool, List[str]]:
    errors = []
    
    if not isinstance(self.my_parameter, str):
        errors.append("myParameter must be a string")
    
    return len(errors) == 0, errors
```

## CLIでの使用

```bash
# カスタムフィルターを使用
video_copy_tool --config config_with_custom_filter.json

# 利用可能なフィルター一覧を表示
video_copy_tool --list-filters

# フィルター設定の詳細統計を表示
video_copy_tool --show-filter-stats --config my_config.json
```

## 拡張例：GPS位置フィルター

特定の地理的位置で撮影された写真のみを含めるフィルターの実装例：

```python
class GpsLocationFilter(BaseFilter):
    def __init__(self, config: Dict[str, Any], filter_id: str):
        super().__init__(config, filter_id)
        self.target_lat = config.get("latitude")
        self.target_lng = config.get("longitude") 
        self.radius_km = config.get("radiusKm", 1.0)
    
    def check_file(self, file_info: FileInfo) -> FilterResult:
        lat = file_info.metadata.get("gps_latitude")
        lng = file_info.metadata.get("gps_longitude")
        
        if not lat or not lng:
            return FilterResult(include=True)  # GPS情報がない場合は含める
        
        distance = self._calculate_distance(lat, lng, self.target_lat, self.target_lng)
        
        if distance <= self.radius_km:
            return FilterResult(
                include=True,
                metadata={"distance_km": distance}
            )
        else:
            return FilterResult(
                include=False,
                reason=f"Outside target area (distance: {distance:.2f}km)",
                metadata={"distance_km": distance}
            )
```

このガイドに従って、プロジェクトのニーズに応じたカスタムフィルターを作成できます。 