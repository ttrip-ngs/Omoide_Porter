import os
import json
import yaml
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """設定ファイルを管理するクラス"""
    
    DEFAULT_CONFIG = {
        "version": "1.0",
        "presets": [],
        "globalSettings": {
            "defaultSource": "",
            "defaultDestination": "",
            "hashAlgorithm": "sha256",
            "cacheHashes": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルトパスを使用）
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    
    def _get_default_config_path(self) -> str:
        """デフォルトの設定ファイルパスを取得"""
        # ユーザーのホームディレクトリ（クロスプラットフォーム対応）
        home_dir = os.path.expanduser("~")
        app_dir = os.path.join(home_dir, ".video_copy_tool")
        
        # 設定ディレクトリが存在しない場合は作成
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        
        return os.path.join(app_dir, "config.json")
    
    def load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込む
        
        Returns:
            設定内容
        """
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}, creating default")
            self.save_config()
            return self.config
        
        try:
            file_ext = os.path.splitext(self.config_path)[1].lower()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if file_ext == '.json':
                    self.config = json.load(f)
                elif file_ext in ['.yml', '.yaml']:
                    self.config = yaml.safe_load(f)
                else:
                    logger.warning(f"Unsupported config file format: {file_ext}")
                    return self.config
            
            logger.info(f"Config loaded from {self.config_path}")
            
            # バージョンチェックやマイグレーションが必要な場合はここで実装
            
            return self.config
        
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return self.config
    
    def save_config(self) -> bool:
        """
        設定をファイルに保存
        
        Returns:
            保存に成功した場合はTrue
        """
        try:
            # 設定ファイルのディレクトリが存在しない場合は作成
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            file_ext = os.path.splitext(self.config_path)[1].lower()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if file_ext == '.json':
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                elif file_ext in ['.yml', '.yaml']:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                else:
                    # デフォルトでJSONとして保存
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Config saved to {self.config_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            return False
    
    def get_preset(self, preset_name: str) -> Optional[Dict[str, Any]]:
        """
        指定した名前のプリセットを取得
        
        Args:
            preset_name: プリセット名
        
        Returns:
            プリセット設定の辞書、存在しない場合はNone
        """
        presets = self.config.get("presets", [])
        for preset in presets:
            if preset.get("name") == preset_name:
                return preset
        return None
    
    def add_preset(self, preset: Dict[str, Any]) -> bool:
        """
        プリセットを追加
        
        Args:
            preset: プリセット設定の辞書
        
        Returns:
            追加に成功した場合はTrue
        """
        preset_name = preset.get("name")
        if not preset_name:
            logger.error("Preset must have a name")
            return False
        
        # 既存のプリセットを更新
        existing_preset = self.get_preset(preset_name)
        if existing_preset:
            presets = self.config.get("presets", [])
            for i, p in enumerate(presets):
                if p.get("name") == preset_name:
                    presets[i] = preset
                    break
        else:
            # 新しいプリセットを追加
            if "presets" not in self.config:
                self.config["presets"] = []
            self.config["presets"].append(preset)
        
        return self.save_config()
    
    def remove_preset(self, preset_name: str) -> bool:
        """
        プリセットを削除
        
        Args:
            preset_name: 削除するプリセット名
        
        Returns:
            削除に成功した場合はTrue
        """
        if "presets" not in self.config:
            return False
        
        presets = self.config["presets"]
        for i, preset in enumerate(presets):
            if preset.get("name") == preset_name:
                presets.pop(i)
                return self.save_config()
        
        return False
    
    def get_global_settings(self) -> Dict[str, Any]:
        """
        グローバル設定を取得
        
        Returns:
            グローバル設定の辞書
        """
        return self.config.get("globalSettings", self.DEFAULT_CONFIG["globalSettings"])
    
    def update_global_settings(self, settings: Dict[str, Any]) -> bool:
        """
        グローバル設定を更新
        
        Args:
            settings: 更新するグローバル設定
        
        Returns:
            更新に成功した場合はTrue
        """
        if "globalSettings" not in self.config:
            self.config["globalSettings"] = {}
        
        # 設定を更新
        for key, value in settings.items():
            self.config["globalSettings"][key] = value
        
        return self.save_config()
    
    def list_presets(self) -> List[str]:
        """
        プリセット名の一覧を取得
        
        Returns:
            プリセット名のリスト
        """
        return [preset.get("name", "") for preset in self.config.get("presets", [])] 