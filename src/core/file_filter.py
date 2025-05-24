import re
import logging
from typing import List, Dict, Any, Optional, Literal

from .file_info import FileInfo

logger = logging.getLogger(__name__)


class FileFilter:
    """ファイルフィルタリング機能を提供するクラス"""
    
    def __init__(self, filter_config: Dict[str, Any]):
        """
        Args:
            filter_config: フィルタ設定辞書
        """
        self.config = filter_config
        self.enabled = filter_config.get("enableFilters", False)
        
        # 基本フィルタ設定
        self.include_media_types = set(filter_config.get("includeMediaTypes", []))
        self.exclude_media_types = set(filter_config.get("excludeMediaTypes", []))
        self.exclude_screenshots = filter_config.get("excludeScreenshots", False)
        
        # スクリーンショット検出設定
        screenshot_config = filter_config.get("screenshotDetection", {})
        self.screenshot_filename_enabled = screenshot_config.get("enableFilenamePattern", True)
        self.screenshot_path_enabled = screenshot_config.get("enablePathPattern", True)
        self.screenshot_metadata_enabled = screenshot_config.get("enableMetadataPattern", True)
        self.screenshot_resolution_enabled = screenshot_config.get("enableResolutionDetection", True)
        self.custom_screenshot_patterns = screenshot_config.get("customPatterns", [])
        
        # その他のフィルタ設定
        self.exclude_by_filename = filter_config.get("excludeByFilename", [])
        self.exclude_by_path = filter_config.get("excludeByPath", [])
        self.min_file_size = filter_config.get("minFileSize", 0)
        self.max_file_size = filter_config.get("maxFileSize")
        self.include_extensions = set(ext.lower() for ext in filter_config.get("includeExtensions", []))
        self.exclude_extensions = set(ext.lower() for ext in filter_config.get("excludeExtensions", []))
    
    def should_include_file(self, file_info: FileInfo) -> bool:
        """
        ファイルがフィルタ条件を満たすかどうかを判定
        
        Args:
            file_info: ファイル情報オブジェクト
            
        Returns:
            ファイルを含める場合True、除外する場合False
        """
        if not self.enabled:
            return True
        
        # メディアタイプによるフィルタリング
        if not self._check_media_type_filter(file_info):
            logger.debug(f"Excluded by media type filter: {file_info.original_filename}")
            return False
        
        # 拡張子によるフィルタリング
        if not self._check_extension_filter(file_info):
            logger.debug(f"Excluded by extension filter: {file_info.original_filename}")
            return False
        
        # ファイルサイズによるフィルタリング
        if not self._check_size_filter(file_info):
            logger.debug(f"Excluded by size filter: {file_info.original_filename}")
            return False
        
        # ファイル名パターンによるフィルタリング
        if not self._check_filename_filter(file_info):
            logger.debug(f"Excluded by filename filter: {file_info.original_filename}")
            return False
        
        # パスパターンによるフィルタリング
        if not self._check_path_filter(file_info):
            logger.debug(f"Excluded by path filter: {file_info.original_filename}")
            return False
        
        # スクリーンショット除外
        if self.exclude_screenshots and self._is_screenshot_by_filter(file_info):
            logger.info(f"Excluded screenshot: {file_info.original_filename}")
            return False
        
        return True
    
    def _check_media_type_filter(self, file_info: FileInfo) -> bool:
        """メディアタイプフィルタをチェック"""
        media_type = file_info.media_type
        
        # 除外リストチェック
        if self.exclude_media_types and media_type in self.exclude_media_types:
            return False
        
        # 包含リストチェック
        if self.include_media_types and media_type not in self.include_media_types:
            return False
        
        return True
    
    def _check_extension_filter(self, file_info: FileInfo) -> bool:
        """拡張子フィルタをチェック"""
        ext = file_info.original_extension.lower()
        
        # 除外リストチェック
        if self.exclude_extensions and ext in self.exclude_extensions:
            return False
        
        # 包含リストチェック
        if self.include_extensions and ext not in self.include_extensions:
            return False
        
        return True
    
    def _check_size_filter(self, file_info: FileInfo) -> bool:
        """ファイルサイズフィルタをチェック"""
        size = file_info.size
        
        if size < self.min_file_size:
            return False
        
        if self.max_file_size is not None and size > self.max_file_size:
            return False
        
        return True
    
    def _check_filename_filter(self, file_info: FileInfo) -> bool:
        """ファイル名パターンフィルタをチェック"""
        filename = file_info.original_filename.lower()
        
        for pattern in self.exclude_by_filename:
            if re.search(pattern.lower(), filename):
                return False
        
        return True
    
    def _check_path_filter(self, file_info: FileInfo) -> bool:
        """パスパターンフィルタをチェック"""
        path = file_info.original_path.lower().replace('\\', '/')
        
        for pattern in self.exclude_by_path:
            if re.search(pattern.lower(), path):
                return False
        
        return True
    
    def _is_screenshot_by_filter(self, file_info: FileInfo) -> bool:
        """
        フィルタ設定に基づいてスクリーンショットかどうかを判定
        
        Args:
            file_info: ファイル情報オブジェクト
            
        Returns:
            スクリーンショットと判定された場合True
        """
        if file_info.media_type != "image":
            return False
        
        # カスタムパターンチェック
        if self._check_custom_screenshot_patterns(file_info):
            return True
        
        # FileInfoのis_screenshot()メソッドを使用しつつ、フィルタ設定を考慮
        # 一時的にFileInfoの設定を上書きして判定
        original_file_info = file_info
        
        # ファイル名パターン判定
        if self.screenshot_filename_enabled:
            if file_info._is_screenshot_by_filename():
                return True
        
        # パスパターン判定
        if self.screenshot_path_enabled:
            if file_info._is_screenshot_by_path():
                return True
        
        # メタデータパターン判定
        if self.screenshot_metadata_enabled:
            if file_info._is_screenshot_by_metadata():
                return True
        
        return False
    
    def _check_custom_screenshot_patterns(self, file_info: FileInfo) -> bool:
        """カスタムスクリーンショットパターンをチェック"""
        filename = file_info.original_filename.lower()
        
        for pattern in self.custom_screenshot_patterns:
            if re.match(pattern.lower(), filename):
                return True
        
        return False
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """フィルタ設定のサマリーを取得"""
        return {
            "enabled": self.enabled,
            "exclude_screenshots": self.exclude_screenshots,
            "include_media_types": list(self.include_media_types),
            "exclude_media_types": list(self.exclude_media_types),
            "include_extensions": list(self.include_extensions),
            "exclude_extensions": list(self.exclude_extensions),
            "min_file_size": self.min_file_size,
            "max_file_size": self.max_file_size,
            "screenshot_detection": {
                "filename_enabled": self.screenshot_filename_enabled,
                "path_enabled": self.screenshot_path_enabled,
                "metadata_enabled": self.screenshot_metadata_enabled,
                "resolution_enabled": self.screenshot_resolution_enabled,
                "custom_patterns_count": len(self.custom_screenshot_patterns)
            }
        }


class FilterStats:
    """フィルタリング統計情報を管理するクラス"""
    
    def __init__(self):
        self.total_files = 0
        self.included_files = 0
        self.excluded_files = 0
        self.excluded_by_media_type = 0
        self.excluded_by_extension = 0
        self.excluded_by_size = 0
        self.excluded_by_filename = 0
        self.excluded_by_path = 0
        self.excluded_screenshots = 0
    
    def add_file(self, included: bool, exclusion_reason: Optional[str] = None):
        """ファイル処理結果を統計に追加"""
        self.total_files += 1
        
        if included:
            self.included_files += 1
        else:
            self.excluded_files += 1
            
            if exclusion_reason == "media_type":
                self.excluded_by_media_type += 1
            elif exclusion_reason == "extension":
                self.excluded_by_extension += 1
            elif exclusion_reason == "size":
                self.excluded_by_size += 1
            elif exclusion_reason == "filename":
                self.excluded_by_filename += 1
            elif exclusion_reason == "path":
                self.excluded_by_path += 1
            elif exclusion_reason == "screenshot":
                self.excluded_screenshots += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """統計サマリーを取得"""
        return {
            "total_files": self.total_files,
            "included_files": self.included_files,
            "excluded_files": self.excluded_files,
            "exclusion_breakdown": {
                "media_type": self.excluded_by_media_type,
                "extension": self.excluded_by_extension,
                "size": self.excluded_by_size,
                "filename": self.excluded_by_filename,
                "path": self.excluded_by_path,
                "screenshots": self.excluded_screenshots
            },
            "inclusion_rate": self.included_files / self.total_files if self.total_files > 0 else 0
        } 