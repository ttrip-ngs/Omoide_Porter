"""
フィルターモジュール

このパッケージは拡張可能なファイルフィルタリングシステムを提供します。
"""

from ..filter_base import filter_registry
from .media_type_filter import MediaTypeFilter
from .screenshot_filter import ScreenshotFilter
from .date_range_filter import DateRangeFilter


def register_default_filters():
    """デフォルトフィルターを登録"""
    
    # 標準フィルターを登録
    filter_registry.register_filter("media_type", MediaTypeFilter)
    filter_registry.register_filter("screenshot", ScreenshotFilter)
    filter_registry.register_filter("date_range", DateRangeFilter)
    
    # 追加の標準フィルター（将来実装予定）
    # filter_registry.register_filter("file_size", FileSizeFilter)
    # filter_registry.register_filter("filename_pattern", FilenamePatternFilter)
    # filter_registry.register_filter("camera_model", CameraModelFilter)
    # filter_registry.register_filter("gps_location", GpsLocationFilter)


def create_filter_chain_from_config(config: dict):
    """設定からフィルターチェーンを作成"""
    return filter_registry.create_filter_chain(config)


# モジュールインポート時にデフォルトフィルターを登録
register_default_filters()


__all__ = [
    'MediaTypeFilter',
    'ScreenshotFilter', 
    'DateRangeFilter',
    'register_default_filters',
    'create_filter_chain_from_config'
] 