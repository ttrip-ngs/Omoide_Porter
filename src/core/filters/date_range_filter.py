"""
日付範囲によるフィルタリング
"""

from datetime import datetime, date
from typing import Dict, Any, Optional, Union
from ..filter_base import BaseFilter, FilterResult
from ..file_info import FileInfo


class DateRangeFilter(BaseFilter):
    """指定された日付範囲内のファイルのみを含めるフィルター"""
    
    def __init__(self, config: Dict[str, Any], filter_id: str):
        super().__init__(config, filter_id)
        
        self.start_date = self._parse_date(config.get("startDate"))
        self.end_date = self._parse_date(config.get("endDate"))
        self.use_metadata_date = config.get("useMetadataDate", True)
        self.use_file_modified_date = config.get("useFileModifiedDate", False)
        self.date_field = config.get("dateField", "datetime")  # メタデータから使用する日付フィールド
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """日付文字列をdatetimeオブジェクトに変換"""
        if not date_str:
            return None
        
        # 複数の日付フォーマットに対応
        formats = [
            "%Y-%m-%d",           # 2024-01-15
            "%Y/%m/%d",           # 2024/01/15
            "%Y-%m-%d %H:%M:%S",  # 2024-01-15 12:30:45
            "%Y:%m:%d %H:%M:%S",  # 2024:01:15 12:30:45 (EXIF形式)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    def check_file(self, file_info: FileInfo) -> FilterResult:
        """日付範囲によるフィルタリング判定"""
        file_date = self._get_file_date(file_info)
        
        if file_date is None:
            return FilterResult(
                include=True,  # 日付不明ファイルは包含
                metadata={"file_date": None, "date_source": "unknown"}
            )
        
        # 日付範囲チェック
        include = True
        exclusion_reason = None
        
        if self.start_date and file_date < self.start_date:
            include = False
            exclusion_reason = f"File date {file_date.strftime('%Y-%m-%d')} is before start date {self.start_date.strftime('%Y-%m-%d')}"
        
        if self.end_date and file_date > self.end_date:
            include = False
            exclusion_reason = f"File date {file_date.strftime('%Y-%m-%d')} is after end date {self.end_date.strftime('%Y-%m-%d')}"
        
        return FilterResult(
            include=include,
            reason=exclusion_reason,
            metadata={
                "file_date": file_date.isoformat(),
                "date_source": self._get_date_source(),
                "start_date": self.start_date.isoformat() if self.start_date else None,
                "end_date": self.end_date.isoformat() if self.end_date else None
            }
        )
    
    def _get_file_date(self, file_info: FileInfo) -> Optional[datetime]:
        """ファイルの日付を取得"""
        
        # メタデータの日付を優先使用
        if self.use_metadata_date and file_info.metadata:
            metadata_date = self._extract_metadata_date(file_info)
            if metadata_date:
                return metadata_date
        
        # ファイルの最終更新日を使用
        if self.use_file_modified_date:
            return file_info.last_modified
        
        return None
    
    def _extract_metadata_date(self, file_info: FileInfo) -> Optional[datetime]:
        """メタデータから日付を抽出"""
        
        # 指定されたフィールドから日付を取得
        date_str = file_info.metadata.get(self.date_field)
        if date_str:
            try:
                return self._parse_date(str(date_str))
            except ValueError:
                pass
        
        # フォールバック: 標準的なEXIF日付フィールドを試行
        fallback_fields = ["datetime", "dateTimeOriginal", "dateTimeDigitized"]
        for field in fallback_fields:
            if field == self.date_field:
                continue  # 既に試行済み
            
            date_str = file_info.metadata.get(field)
            if date_str:
                try:
                    return self._parse_date(str(date_str))
                except ValueError:
                    continue
        
        return None
    
    def _get_date_source(self) -> str:
        """使用している日付ソースを取得"""
        if self.use_metadata_date:
            return f"metadata_{self.date_field}"
        elif self.use_file_modified_date:
            return "file_modified"
        else:
            return "unknown"
    
    def get_filter_name(self) -> str:
        return "Date Range Filter"
    
    def get_filter_description(self) -> str:
        parts = []
        if self.start_date:
            parts.append(f"from {self.start_date.strftime('%Y-%m-%d')}")
        if self.end_date:
            parts.append(f"to {self.end_date.strftime('%Y-%m-%d')}")
        
        date_range = " ".join(parts) if parts else "all dates"
        date_source = self._get_date_source()
        
        return f"Includes files {date_range} (using {date_source})"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "startDate": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date (YYYY-MM-DD format)"
                },
                "endDate": {
                    "type": "string",
                    "format": "date", 
                    "description": "End date (YYYY-MM-DD format)"
                },
                "useMetadataDate": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use date from file metadata (EXIF, etc.)"
                },
                "useFileModifiedDate": {
                    "type": "boolean",
                    "default": False,
                    "description": "Use file system modification date as fallback"
                },
                "dateField": {
                    "type": "string",
                    "default": "datetime",
                    "description": "Metadata field to use for date extraction"
                },
                "enabled": {"type": "boolean", "default": True},
                "priority": {"type": "integer", "default": 30}
            }
        } 