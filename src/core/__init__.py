"""
動画・写真コピーユーティリティのコアロジックモジュール

このパッケージは以下のモジュールを含みます：

- file_info: ファイル情報を管理するクラス
- metadata_extractor: メタデータを抽出するクラス
- path_generator: パスとファイル名を生成するクラス
- config_manager: 設定ファイルを管理するクラス
- file_operations: ファイル操作（コピー、重複チェックなど）を行うクラス
- file_filter: ファイルフィルタリング機能を提供するクラス
"""

from .file_info import FileInfo
from .metadata_extractor import MetadataExtractor
from .path_generator import (
    PathElement, LiteralElement, MetadataElement, 
    OriginalFilenameElement, SequenceElement, PathGenerator
)
from .config_manager import ConfigManager
from .file_operations import FileOperations
from .file_filter import FileFilter, FilterStats

__all__ = [
    'FileInfo',
    'MetadataExtractor',
    'PathElement',
    'LiteralElement',
    'MetadataElement',
    'OriginalFilenameElement',
    'SequenceElement',
    'PathGenerator',
    'ConfigManager',
    'FileOperations',
    'FileFilter',
    'FilterStats',
] 