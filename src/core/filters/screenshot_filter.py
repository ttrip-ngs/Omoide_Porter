"""
スクリーンショット除外フィルター
"""

from typing import Dict, Any, List
from ..filter_base import BaseFilter, FilterResult
from ..file_info import FileInfo


class ScreenshotFilter(BaseFilter):
    """スクリーンショットファイルの除外フィルター"""
    
    def __init__(self, config: Dict[str, Any], filter_id: str):
        super().__init__(config, filter_id)
        
        self.exclude_screenshots = config.get("excludeScreenshots", True)
        
        # スクリーンショット検出設定
        detection_config = config.get("detection", {})
        self.enable_filename_pattern = detection_config.get("enableFilenamePattern", True)
        self.enable_path_pattern = detection_config.get("enablePathPattern", True)
        self.enable_metadata_pattern = detection_config.get("enableMetadataPattern", True)
        self.enable_resolution_detection = detection_config.get("enableResolutionDetection", True)
        self.custom_patterns: List[str] = detection_config.get("customPatterns", [])
        
        # デバイス特有設定
        self.device_type = config.get("deviceType", "auto")  # iOS, Android, auto
    
    def check_file(self, file_info: FileInfo) -> FilterResult:
        """スクリーンショット判定によるフィルタリング"""
        if not self.exclude_screenshots:
            return FilterResult(include=True)
        
        # 画像以外はスクリーンショットではない
        if file_info.media_type != "image":
            return FilterResult(include=True, metadata={"is_screenshot": False})
        
        # スクリーンショット判定実行
        is_screenshot, detection_method = self._detect_screenshot(file_info)
        
        if is_screenshot:
            return FilterResult(
                include=False,
                reason=f"Screenshot detected by {detection_method}",
                metadata={
                    "is_screenshot": True,
                    "detection_method": detection_method,
                    "device_type": self.device_type
                }
            )
        
        return FilterResult(
            include=True,
            metadata={"is_screenshot": False}
        )
    
    def _detect_screenshot(self, file_info: FileInfo) -> tuple[bool, str]:
        """スクリーンショット検出を実行"""
        
        # カスタムパターンチェック
        if self.custom_patterns:
            for pattern in self.custom_patterns:
                import re
                if re.match(pattern.lower(), file_info.original_filename.lower()):
                    return True, "custom_pattern"
        
        # ファイル名パターン判定
        if self.enable_filename_pattern:
            if file_info._is_screenshot_by_filename():
                return True, "filename_pattern"
        
        # パスパターン判定
        if self.enable_path_pattern:
            if file_info._is_screenshot_by_path():
                return True, "path_pattern"
        
        # メタデータパターン判定
        if self.enable_metadata_pattern:
            if file_info._is_screenshot_by_metadata():
                return True, "metadata_pattern"
        
        # 解像度判定（デバイス特有）
        if self.enable_resolution_detection:
            if self._detect_by_resolution(file_info):
                return True, "resolution_pattern"
        
        return False, "none"
    
    def _detect_by_resolution(self, file_info: FileInfo) -> bool:
        """解像度によるスクリーンショット検出"""
        width = file_info.metadata.get('width', 0)
        height = file_info.metadata.get('height', 0)
        
        if not width or not height:
            return False
        
        # PNGファイルのみ対象
        if file_info.original_extension.lower() != 'png':
            return False
        
        # iOSデバイスの画面解像度
        ios_resolutions = [
            (1125, 2436), (1242, 2688), (828, 1792),  # iPhone X系
            (750, 1334), (1242, 2208),  # iPhone 6/7/8系
            (640, 1136), (640, 960), (320, 480),  # 古いiPhone
            (1668, 2388), (2048, 2732), (1536, 2048),  # iPad
        ]
        
        # Android一般的解像度（参考値）
        android_resolutions = [
            (1080, 1920), (1440, 2560), (1080, 2340),
            (720, 1280), (1080, 2160), (1440, 3120),
        ]
        
        all_resolutions = ios_resolutions + android_resolutions
        
        # デバイスタイプ指定がある場合は該当するもののみチェック
        if self.device_type == "iOS":
            check_resolutions = ios_resolutions
        elif self.device_type == "Android":
            check_resolutions = android_resolutions
        else:
            check_resolutions = all_resolutions
        
        # 縦横どちらでも一致すればスクリーンショットの可能性
        for w, h in check_resolutions:
            if (width == w and height == h) or (width == h and height == w):
                return True
        
        return False
    
    def get_filter_name(self) -> str:
        return "Screenshot Filter"
    
    def get_filter_description(self) -> str:
        if self.exclude_screenshots:
            methods = []
            if self.enable_filename_pattern:
                methods.append("filename")
            if self.enable_path_pattern:
                methods.append("path")
            if self.enable_metadata_pattern:
                methods.append("metadata")
            if self.enable_resolution_detection:
                methods.append("resolution")
            
            return f"Excludes screenshot files using detection methods: {', '.join(methods)}"
        else:
            return "Screenshot filtering disabled"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "excludeScreenshots": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to exclude screenshot files"
                },
                "deviceType": {
                    "type": "string",
                    "enum": ["auto", "iOS", "Android"],
                    "default": "auto",
                    "description": "Device type for optimized detection"
                },
                "detection": {
                    "type": "object",
                    "properties": {
                        "enableFilenamePattern": {"type": "boolean", "default": True},
                        "enablePathPattern": {"type": "boolean", "default": True},
                        "enableMetadataPattern": {"type": "boolean", "default": True},
                        "enableResolutionDetection": {"type": "boolean", "default": True},
                        "customPatterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Custom regex patterns for screenshot detection"
                        }
                    }
                },
                "enabled": {"type": "boolean", "default": True},
                "priority": {"type": "integer", "default": 50}
            }
        } 