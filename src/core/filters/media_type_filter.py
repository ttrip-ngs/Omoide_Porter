"""
メディアタイプによるフィルタリング
"""

from typing import Dict, Any, Set
from ..filter_base import BaseFilter, FilterResult
from ..file_info import FileInfo


class MediaTypeFilter(BaseFilter):
    """メディアタイプによるファイルフィルター"""
    
    def __init__(self, config: Dict[str, Any], filter_id: str):
        super().__init__(config, filter_id)
        
        self.include_types: Set[str] = set(config.get("includeTypes", []))
        self.exclude_types: Set[str] = set(config.get("excludeTypes", []))
    
    def check_file(self, file_info: FileInfo) -> FilterResult:
        """メディアタイプによるフィルタリング判定"""
        media_type = file_info.media_type
        
        # 除外リストチェック
        if self.exclude_types and media_type in self.exclude_types:
            return FilterResult(
                include=False,
                reason=f"Excluded media type: {media_type}",
                metadata={"excluded_type": media_type}
            )
        
        # 包含リストチェック
        if self.include_types and media_type not in self.include_types:
            return FilterResult(
                include=False,
                reason=f"Not in included media types: {media_type}",
                metadata={"media_type": media_type, "allowed_types": list(self.include_types)}
            )
        
        return FilterResult(
            include=True,
            metadata={"media_type": media_type}
        )
    
    def get_filter_name(self) -> str:
        return "Media Type Filter"
    
    def get_filter_description(self) -> str:
        include_desc = f"Include: {list(self.include_types)}" if self.include_types else "Include: All"
        exclude_desc = f"Exclude: {list(self.exclude_types)}" if self.exclude_types else "Exclude: None"
        return f"Filters files by media type. {include_desc}, {exclude_desc}"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "includeTypes": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["image", "video", "audio", "raw", "unknown"]},
                    "description": "Media types to include (empty means include all)"
                },
                "excludeTypes": {
                    "type": "array", 
                    "items": {"type": "string", "enum": ["image", "video", "audio", "raw", "unknown"]},
                    "description": "Media types to exclude"
                },
                "enabled": {"type": "boolean", "default": True},
                "priority": {"type": "integer", "default": 10}
            }
        } 