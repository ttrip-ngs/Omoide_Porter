import os
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime

from .file_info import FileInfo


class PathElement:
    """パス要素の基底クラス"""
    
    def generate(self, file_info: FileInfo) -> str:
        """パス要素を生成"""
        raise NotImplementedError("サブクラスで実装する必要があります")


class LiteralElement(PathElement):
    """固定文字列要素"""
    
    def __init__(self, value: str):
        self.value = value
    
    def generate(self, file_info: FileInfo) -> str:
        return self.value


class MetadataElement(PathElement):
    """メタデータ要素"""
    
    def __init__(self, key: str):
        self.key = key
    
    def generate(self, file_info: FileInfo) -> str:
        # 特殊な日時フォーマット
        if self.key == "datetime":
            # メタデータから日時情報を取得
            dt_str = file_info.metadata.get("datetime")
            if dt_str:
                try:
                    # EXIF形式 (2023:01:15 12:30:45) を処理
                    dt_str = dt_str.replace(":", "").replace(" ", "_")
                    return dt_str
                except Exception:
                    pass
            # 日時情報がない場合はファイルの最終更新日時を使用
            return file_info.last_modified.strftime("%Y%m%d_%H%M%S")
        
        # 基本的なメタデータフィールド
        value = file_info.metadata.get(self.key)
        if value:
            # 特殊文字を置換
            value = str(value).strip()
            # パスに使えない文字を置換
            value = re.sub(r'[<>:"/\\|?*]', "_", value)
            return value
        
        # メタデータがない場合のデフォルト値
        defaults = {
            "year": lambda: file_info.last_modified.strftime("%Y"),
            "month": lambda: file_info.last_modified.strftime("%m"),
            "day": lambda: file_info.last_modified.strftime("%d"),
            "camera_make": lambda: "Unknown",
            "camera_model": lambda: "Unknown"
        }
        
        if self.key in defaults:
            return defaults[self.key]()
        
        return "Unknown"


class OriginalFilenameElement(PathElement):
    """元のファイル名要素"""
    
    def generate(self, file_info: FileInfo) -> str:
        name, _ = os.path.splitext(file_info.original_filename)
        return name


class SequenceElement(PathElement):
    """連番要素"""
    
    def __init__(self, digits: int = 3):
        self.digits = digits
        self._counter = 0
    
    def generate(self, file_info: FileInfo) -> str:
        self._counter += 1
        return f"{self._counter:0{self.digits}d}"


class PathGenerator:
    """パスとファイル名を生成するクラス"""
    
    @staticmethod
    def parse_folder_structure(structure: List[Dict[str, Any]]) -> List[PathElement]:
        """
        フォルダ構造定義をパス要素のリストに変換
        
        Args:
            structure: 設定ファイルから読み込んだフォルダ構造定義
            
        Returns:
            パス要素のリスト
        """
        elements = []
        
        for item in structure:
            element_type = item.get("type", "")
            
            if element_type == "literal":
                elements.append(LiteralElement(item.get("value", "")))
            elif element_type == "metadata":
                elements.append(MetadataElement(item.get("value", "")))
            elif element_type == "sequence":
                digits = int(item.get("digits", 3))
                elements.append(SequenceElement(digits))
            
        return elements
    
    @staticmethod
    def parse_filename_pattern(pattern: List[Dict[str, Any]]) -> List[PathElement]:
        """
        ファイル名パターン定義をパス要素のリストに変換
        
        Args:
            pattern: 設定ファイルから読み込んだファイル名パターン定義
            
        Returns:
            パス要素のリスト
        """
        elements = []
        
        for item in pattern:
            element_type = item.get("type", "")
            
            if element_type == "literal":
                elements.append(LiteralElement(item.get("value", "")))
            elif element_type == "metadata":
                elements.append(MetadataElement(item.get("value", "")))
            elif element_type == "original_filename":
                elements.append(OriginalFilenameElement())
            elif element_type == "sequence":
                digits = int(item.get("digits", 3))
                elements.append(SequenceElement(digits))
            
        return elements
    
    @staticmethod
    def generate_folder_path(
        file_info: FileInfo,
        folder_elements: List[PathElement],
        destination_root: str
    ) -> str:
        """
        フォルダパスを生成
        
        Args:
            file_info: ファイル情報
            folder_elements: フォルダ構造のパス要素リスト
            destination_root: コピー先のルートディレクトリ
            
        Returns:
            生成されたフォルダパス
        """
        path_parts = []
        
        for element in folder_elements:
            part = element.generate(file_info)
            if part:
                # パスに使えない文字を置換
                part = re.sub(r'[<>:"/\\|?*]', "_", part)
                path_parts.append(part)
        
        # パーツを結合してフォルダパスを生成
        folder_path = os.path.join(destination_root, *path_parts)
        return folder_path
    
    @staticmethod
    def generate_filename(
        file_info: FileInfo,
        filename_elements: List[PathElement]
    ) -> str:
        """
        ファイル名を生成
        
        Args:
            file_info: ファイル情報
            filename_elements: ファイル名パターンのパス要素リスト
            
        Returns:
            生成されたファイル名（拡張子付き）
        """
        # 拡張子を取得
        extension = file_info.original_extension
        
        # ファイル名のパーツを生成
        filename_parts = []
        for element in filename_elements:
            part = element.generate(file_info)
            if part:
                # ファイル名に使えない文字を置換
                part = re.sub(r'[<>:"/\\|?*]', "_", part)
                filename_parts.append(part)
        
        # パーツを結合してファイル名を生成
        filename = "".join(filename_parts)
        
        # ファイル名が空の場合はデフォルト名を使用
        if not filename:
            filename = "file"
        
        return f"{filename}.{extension}"
    
    @staticmethod
    def generate_target_path(
        file_info: FileInfo,
        folder_elements: List[PathElement],
        filename_elements: List[PathElement],
        destination_root: str
    ) -> str:
        """
        コピー先のフルパスを生成
        
        Args:
            file_info: ファイル情報
            folder_elements: フォルダ構造のパス要素リスト
            filename_elements: ファイル名パターンのパス要素リスト
            destination_root: コピー先のルートディレクトリ
            
        Returns:
            生成されたフルパス
        """
        folder_path = PathGenerator.generate_folder_path(
            file_info, folder_elements, destination_root
        )
        filename = PathGenerator.generate_filename(file_info, filename_elements)
        
        return os.path.join(folder_path, filename)
    
    @staticmethod
    def resolve_path_conflicts(
        target_path: str,
        file_info: FileInfo
    ) -> str:
        """
        パスの衝突を解決
        
        Args:
            target_path: 生成されたパス
            file_info: ファイル情報
            
        Returns:
            衝突が解決されたパス
        """
        if not os.path.exists(target_path):
            return target_path
        
        # パスが存在する場合、連番を付けて衝突を回避
        base_path, extension = os.path.splitext(target_path)
        counter = 1
        
        while True:
            new_path = f"{base_path}_{counter}{extension}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1 