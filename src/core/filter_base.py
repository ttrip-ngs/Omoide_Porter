"""
フィルターシステムの基底クラスとインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import logging

from .file_info import FileInfo

logger = logging.getLogger(__name__)


class FilterResult:
    """フィルタ判定結果を表すクラス"""
    
    def __init__(self, include: bool, reason: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Args:
            include: ファイルを含める場合True、除外する場合False
            reason: 除外理由（除外時のみ）
            metadata: フィルタ固有の追加情報
        """
        self.include = include
        self.reason = reason
        self.metadata = metadata or {}


class BaseFilter(ABC):
    """ファイルフィルターの基底クラス"""
    
    def __init__(self, config: Dict[str, Any], filter_id: str):
        """
        Args:
            config: フィルター設定辞書
            filter_id: フィルターの一意識別子
        """
        self.config = config
        self.filter_id = filter_id
        self.enabled = config.get("enabled", True)
        self.priority = config.get("priority", 100)  # 優先度（小さいほど先に実行）
    
    @abstractmethod
    def check_file(self, file_info: FileInfo) -> FilterResult:
        """
        ファイルがフィルタ条件を満たすかどうかを判定
        
        Args:
            file_info: ファイル情報オブジェクト
            
        Returns:
            フィルタ判定結果
        """
        pass
    
    @abstractmethod
    def get_filter_name(self) -> str:
        """フィルター名を取得"""
        pass
    
    @abstractmethod
    def get_filter_description(self) -> str:
        """フィルターの説明を取得"""
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """設定スキーマを取得（オプション）"""
        return {}
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """設定の妥当性をチェック"""
        return True, []


class FilterChain:
    """複数のフィルターを順次実行するチェインクラス"""
    
    def __init__(self):
        self.filters: List[BaseFilter] = []
        self.stats = FilterStats()
    
    def add_filter(self, filter_instance: BaseFilter) -> None:
        """フィルターをチェインに追加"""
        if filter_instance.enabled:
            self.filters.append(filter_instance)
            # 優先度順にソート
            self.filters.sort(key=lambda f: f.priority)
    
    def should_include_file(self, file_info: FileInfo) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        ファイルがフィルタチェーンを通過するかどうかを判定
        
        Args:
            file_info: ファイル情報オブジェクト
            
        Returns:
            (含める場合True, 除外理由, フィルタメタデータ)
        """
        filter_metadata = {}
        
        for filter_instance in self.filters:
            result = filter_instance.check_file(file_info)
            
            # フィルタメタデータを蓄積
            filter_metadata[filter_instance.filter_id] = result.metadata
            
            if not result.include:
                self.stats.add_file(False, filter_instance.filter_id)
                return False, result.reason, filter_metadata
        
        self.stats.add_file(True)
        return True, None, filter_metadata
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """フィルタチェーンのサマリーを取得"""
        return {
            "active_filters": [
                {
                    "id": f.filter_id,
                    "name": f.get_filter_name(),
                    "priority": f.priority
                }
                for f in self.filters
            ],
            "total_filters": len(self.filters),
            "stats": self.stats.get_summary()
        }


class FilterStats:
    """フィルタリング統計情報を管理するクラス"""
    
    def __init__(self):
        self.total_files = 0
        self.included_files = 0
        self.excluded_files = 0
        self.exclusion_by_filter = {}  # filter_id -> count
    
    def add_file(self, included: bool, filter_id: Optional[str] = None):
        """ファイル処理結果を統計に追加"""
        self.total_files += 1
        
        if included:
            self.included_files += 1
        else:
            self.excluded_files += 1
            if filter_id:
                self.exclusion_by_filter[filter_id] = self.exclusion_by_filter.get(filter_id, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """統計サマリーを取得"""
        return {
            "total_files": self.total_files,
            "included_files": self.included_files,
            "excluded_files": self.excluded_files,
            "exclusion_by_filter": self.exclusion_by_filter,
            "inclusion_rate": self.included_files / self.total_files if self.total_files > 0 else 0
        }


class FilterRegistry:
    """フィルタープラグインの登録と管理を行うクラス"""
    
    def __init__(self):
        self._filter_classes = {}
    
    def register_filter(self, filter_id: str, filter_class: type) -> None:
        """フィルタークラスを登録"""
        if not issubclass(filter_class, BaseFilter):
            raise ValueError(f"Filter class must inherit from BaseFilter: {filter_class}")
        
        self._filter_classes[filter_id] = filter_class
        logger.info(f"Registered filter: {filter_id}")
    
    def create_filter(self, filter_id: str, config: Dict[str, Any]) -> BaseFilter:
        """フィルターインスタンスを作成"""
        if filter_id not in self._filter_classes:
            raise ValueError(f"Unknown filter ID: {filter_id}")
        
        filter_class = self._filter_classes[filter_id]
        return filter_class(config, filter_id)
    
    def get_available_filters(self) -> List[str]:
        """利用可能なフィルターIDのリストを取得"""
        return list(self._filter_classes.keys())
    
    def create_filter_chain(self, filters_config: Dict[str, Dict[str, Any]]) -> FilterChain:
        """設定からフィルターチェーンを作成"""
        chain = FilterChain()
        
        for filter_id, filter_config in filters_config.items():
            try:
                filter_instance = self.create_filter(filter_id, filter_config)
                chain.add_filter(filter_instance)
            except Exception as e:
                logger.error(f"Failed to create filter {filter_id}: {e}")
        
        return chain


# グローバルフィルタレジストリインスタンス
filter_registry = FilterRegistry() 