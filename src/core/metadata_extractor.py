import os
import exifread
from tinytag import TinyTag
from typing import Dict, Any, Optional
import logging
from PIL import Image

from .file_info import FileInfo

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """ファイルからメタデータを抽出するクラス"""

    @staticmethod
    def extract_metadata(file_info: FileInfo) -> Dict[str, Any]:
        """
        ファイルからメタデータを抽出
        
        Args:
            file_info: ファイル情報オブジェクト
            
        Returns:
            メタデータの辞書
        """
        if not os.path.exists(file_info.original_path):
            logger.error(f"File not found: {file_info.original_path}")
            return {}
        
        metadata = {}
        
        try:
            if file_info.media_type == "image" or file_info.media_type == "raw":
                metadata = MetadataExtractor._extract_image_metadata(file_info.original_path)
            elif file_info.media_type == "video" or file_info.media_type == "audio":
                metadata = MetadataExtractor._extract_audio_video_metadata(file_info.original_path)
        except Exception as e:
            logger.error(f"Failed to extract metadata: {str(e)}")
        
        file_info.metadata = metadata
        
        # メタデータ更新後にスクリーンショット判定キャッシュをリセット
        file_info.reset_screenshot_cache()
        
        return metadata
    
    @staticmethod
    def _extract_image_metadata(file_path: str) -> Dict[str, Any]:
        """画像ファイルからメタデータを抽出"""
        metadata = {}
        
        try:
            # PILを使用して基本的な画像情報を取得
            with Image.open(file_path) as img:
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['format'] = img.format
        except Exception as e:
            logger.warning(f"Failed to get image dimensions with PIL: {str(e)}")
        
        try:
            # exifreadを使用してEXIFデータを抽出
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                
                # 日時情報
                if 'EXIF DateTimeOriginal' in tags:
                    dt_str = str(tags['EXIF DateTimeOriginal'])
                    metadata['datetime'] = dt_str
                    parts = dt_str.split(' ')[0].split(':')
                    metadata['year'] = parts[0]
                    metadata['month'] = parts[1]
                    metadata['day'] = parts[2]
                
                # カメラ情報
                if 'Image Make' in tags:
                    metadata['camera_make'] = str(tags['Image Make'])
                if 'Image Model' in tags:
                    metadata['camera_model'] = str(tags['Image Model'])
                
                # レンズ情報
                if 'EXIF LensModel' in tags:
                    metadata['lens_model'] = str(tags['EXIF LensModel'])
                
                # GPS情報
                if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                    metadata['gps_latitude'] = str(tags['GPS GPSLatitude'])
                    metadata['gps_longitude'] = str(tags['GPS GPSLongitude'])
                
                # スクリーンショット判定用のメタデータ
                if 'Image ImageDescription' in tags:
                    metadata['image_description'] = str(tags['Image ImageDescription'])
                
                if 'Image Software' in tags:
                    metadata['software'] = str(tags['Image Software'])
                
                # EXIF内の画像サイズ（PILで取得できない場合の補完）
                if 'EXIF ExifImageWidth' in tags and 'width' not in metadata:
                    metadata['width'] = int(str(tags['EXIF ExifImageWidth']))
                if 'EXIF ExifImageLength' in tags and 'height' not in metadata:
                    metadata['height'] = int(str(tags['EXIF ExifImageLength']))
        
        except Exception as e:
            logger.error(f"Error extracting EXIF metadata: {str(e)}")
        
        return metadata
    
    @staticmethod
    def _extract_audio_video_metadata(file_path: str) -> Dict[str, Any]:
        """動画・音声ファイルからメタデータを抽出"""
        metadata = {}
        
        try:
            # TinyTagを使用してメタデータを抽出
            tag = TinyTag.get(file_path)
            
            # 日時情報（利用可能であれば）
            if tag.year:
                metadata['year'] = str(tag.year)
            if tag.date:
                metadata['datetime'] = str(tag.date)
            
            # その他利用可能なタグ
            for field in ['title', 'artist', 'album', 'albumartist', 'composer']:
                value = getattr(tag, field, None)
                if value:
                    metadata[field] = str(value)
        
        except Exception as e:
            logger.error(f"Error extracting audio/video metadata: {str(e)}")
        
        return metadata
    
    @staticmethod
    def find_associated_files(
        file_info: FileInfo,
        source_dir: str,
        extensions: list[str]
    ) -> list[FileInfo]:
        """
        関連ファイルを検索
        
        Args:
            file_info: メインのファイル情報
            source_dir: 検索対象ディレクトリ
            extensions: 関連ファイルとみなす拡張子のリスト
            
        Returns:
            関連ファイルのFileInfoオブジェクトのリスト
        """
        associated_files = []
        
        if not os.path.exists(source_dir):
            return associated_files
        
        # 拡張子を除いたファイル名（ベース名）
        base_name = os.path.splitext(file_info.original_filename)[0]
        
        # 同じディレクトリ内のファイルをスキャン
        for filename in os.listdir(source_dir):
            # すでに対象のファイル自体である場合はスキップ
            if filename == file_info.original_filename:
                continue
            
            # ベース名が一致し、拡張子が指定リストにあるファイルを探す
            file_base, file_ext = os.path.splitext(filename)
            if file_base == base_name and file_ext[1:].lower() in [ext.lower() for ext in extensions]:
                full_path = os.path.join(source_dir, filename)
                associated_file = FileInfo(full_path)
                associated_files.append(associated_file)
        
        return associated_files 