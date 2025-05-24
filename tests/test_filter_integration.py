"""
新しいフィルターシステムの統合テスト
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.file_info import FileInfo
from src.core.filter_base import FilterRegistry, FilterChain
from src.core.filters.media_type_filter import MediaTypeFilter
from src.core.filters.screenshot_filter import ScreenshotFilter
from src.core.filters.date_range_filter import DateRangeFilter
from src.core.filters import create_filter_chain_from_config


class TestFilterIntegration(unittest.TestCase):
    """フィルターシステム統合テスト"""
    
    def setUp(self):
        """テストセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        
        # テスト用のファイル情報を作成
        self.test_files = [
            # 通常の画像ファイル
            self._create_test_file("photo001.jpg", "image", {"datetime": "2024:01:15 12:30:45"}),
            
            # スクリーンショット
            self._create_test_file("IMG_0123.PNG", "image", {"width": 750, "height": 1334}),
            
            # 動画ファイル
            self._create_test_file("video001.mp4", "video", {"datetime": "2024:06:15 14:20:30"}),
            
            # 古い写真
            self._create_test_file("old_photo.jpg", "image", {"datetime": "2020:12:01 10:15:20"}),
            
            # RAWファイル
            self._create_test_file("raw_image.arw", "raw", {"datetime": "2024:02:20 16:45:10"}),
        ]
    
    def _create_test_file(self, filename: str, media_type: str, metadata: dict = None) -> FileInfo:
        """テスト用FileInfoオブジェクトを作成"""
        file_path = os.path.join(self.temp_dir, filename)
        
        # 実際のファイルを作成
        with open(file_path, 'w') as f:
            f.write("test content")
        
        file_info = FileInfo(file_path)
        file_info.media_type = media_type
        file_info.metadata = metadata or {}
        
        return file_info
    
    def test_media_type_filter(self):
        """メディアタイプフィルターのテスト"""
        config = {
            "includeTypes": ["image", "video"],
            "excludeTypes": []
        }
        
        filter_instance = MediaTypeFilter(config, "media_type")
        
        # 画像ファイルは通る
        result = filter_instance.check_file(self.test_files[0])
        self.assertTrue(result.include)
        
        # RAWファイルは除外される
        result = filter_instance.check_file(self.test_files[4])
        self.assertFalse(result.include)
    
    def test_screenshot_filter(self):
        """スクリーンショットフィルターのテスト"""
        config = {
            "excludeScreenshots": True,
            "deviceType": "iOS",
            "detection": {
                "enableFilenamePattern": True,
                "enableResolutionDetection": True
            }
        }
        
        filter_instance = ScreenshotFilter(config, "screenshot")
        
        # 通常の写真は通る
        result = filter_instance.check_file(self.test_files[0])
        self.assertTrue(result.include)
        
        # スクリーンショットは除外される
        result = filter_instance.check_file(self.test_files[1])
        self.assertFalse(result.include)
        self.assertEqual(result.metadata["detection_method"], "filename_pattern")
    
    def test_date_range_filter(self):
        """日付範囲フィルターのテスト"""
        config = {
            "startDate": "2024-01-01",
            "endDate": "2024-12-31",
            "useMetadataDate": True,
            "dateField": "datetime"
        }
        
        filter_instance = DateRangeFilter(config, "date_range")
        
        # 2024年の写真は通る
        result = filter_instance.check_file(self.test_files[0])
        self.assertTrue(result.include)
        
        # 2020年の写真は除外される
        result = filter_instance.check_file(self.test_files[3])
        self.assertFalse(result.include)
    
    def test_filter_chain(self):
        """フィルターチェーンのテスト"""
        filters_config = {
            "media_type": {
                "enabled": True,
                "priority": 10,
                "includeTypes": ["image", "video"],
                "excludeTypes": []
            },
            "screenshot": {
                "enabled": True,
                "priority": 50,
                "excludeScreenshots": True,
                "deviceType": "iOS"
            },
            "date_range": {
                "enabled": True,
                "priority": 30,
                "startDate": "2024-01-01",
                "endDate": "2024-12-31",
                "useMetadataDate": True
            }
        }
        
        filter_chain = create_filter_chain_from_config(filters_config)
        
        # 各ファイルをテスト
        results = []
        for file_info in self.test_files:
            include, reason, metadata = filter_chain.should_include_file(file_info)
            results.append((file_info.original_filename, include, reason))
        
        # 期待される結果
        expected = [
            ("photo001.jpg", True, None),        # 通常の2024年の画像 → 通る
            ("IMG_0123.PNG", False, "Screenshot detected by filename_pattern"),  # スクリーンショット → 除外
            ("video001.mp4", True, None),        # 2024年の動画 → 通る
            ("old_photo.jpg", False, "File date 2020-12-01 is before start date 2024-01-01"),  # 古い写真 → 除外
            ("raw_image.arw", False, "Not in included media types: raw"),  # RAWファイル → 除外
        ]
        
        self.assertEqual(len(results), len(expected))
        for i, (filename, include, reason) in enumerate(expected):
            self.assertEqual(results[i][0], filename)
            self.assertEqual(results[i][1], include)
            if not include:
                self.assertIsNotNone(results[i][2])
    
    def test_filter_registry(self):
        """フィルターレジストリのテスト"""
        registry = FilterRegistry()
        
        # フィルターを登録
        registry.register_filter("media_type", MediaTypeFilter)
        registry.register_filter("screenshot", ScreenshotFilter)
        
        # 利用可能なフィルターを確認
        available = registry.get_available_filters()
        self.assertIn("media_type", available)
        self.assertIn("screenshot", available)
        
        # フィルターインスタンスを作成
        config = {"includeTypes": ["image"]}
        filter_instance = registry.create_filter("media_type", config)
        self.assertIsInstance(filter_instance, MediaTypeFilter)
    
    def test_filter_priority(self):
        """フィルター実行順序のテスト"""
        filters_config = {
            "screenshot": {
                "enabled": True,
                "priority": 50,  # 後で実行
                "excludeScreenshots": True
            },
            "media_type": {
                "enabled": True,
                "priority": 10,  # 先に実行
                "includeTypes": ["image"]
            }
        }
        
        filter_chain = create_filter_chain_from_config(filters_config)
        
        # フィルターが優先度順に並んでいることを確認
        self.assertEqual(len(filter_chain.filters), 2)
        self.assertEqual(filter_chain.filters[0].priority, 10)  # media_type
        self.assertEqual(filter_chain.filters[1].priority, 50)  # screenshot
    
    def tearDown(self):
        """テストクリーンアップ"""
        # テンポラリファイルを削除
        for file_info in self.test_files:
            if os.path.exists(file_info.original_path):
                os.remove(file_info.original_path)
        
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)


if __name__ == "__main__":
    unittest.main() 