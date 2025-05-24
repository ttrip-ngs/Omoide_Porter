"""
設定管理システム
アプリケーションの設定とプリセットを管理
"""

import json
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from loguru import logger

from .models import DeviceProfile, DeviceType, TransferProtocol


class DuplicateHandling(Enum):
    """重複ファイル処理方法"""
    SKIP = "skip"
    OVERWRITE = "overwrite" 
    RENAME = "rename"
    ASK = "ask"


class ConflictResolutionType(Enum):
    """ファイル名衝突解決方法"""
    SEQUENCE = "sequence"
    TIMESTAMP = "timestamp"


@dataclass
class FolderLevel:
    """フォルダレベル設定"""
    type: str  # literal, metadata, sequence
    field: Optional[str] = None
    format: Optional[str] = None
    value: Optional[str] = None


@dataclass
class FolderStructure:
    """フォルダ構造設定"""
    levels: List[FolderLevel] = field(default_factory=list)
    separator: str = "/"


@dataclass
class FileNameComponent:
    """ファイル名コンポーネント"""
    type: str  # literal, metadata, original_filename, original_extension, sequence
    field: Optional[str] = None
    format: Optional[str] = None
    value: Optional[str] = None
    include_extension: bool = False


@dataclass
class ConflictResolution:
    """ファイル名衝突解決設定"""
    type: ConflictResolutionType = ConflictResolutionType.SEQUENCE
    digits: int = 3
    position: str = "before_extension"  # before_extension, after_name


@dataclass
class FileNamePattern:
    """ファイル名パターン設定"""
    components: List[FileNameComponent] = field(default_factory=list)
    conflict_resolution: ConflictResolution = field(default_factory=ConflictResolution)


@dataclass
class AssociatedFileRules:
    """関連ファイル認識ルール"""
    same_base_name: List[str] = field(default_factory=lambda: ["xmp", "thm", "aae"])
    video_to_image: List[str] = field(default_factory=lambda: ["jpg", "jpeg"])
    custom_patterns: List[str] = field(default_factory=list)


@dataclass
class DeviceSettings:
    """デバイス設定"""
    auto_detect_devices: bool = True
    enable_device_notifications: bool = True
    connection_timeout: int = 30
    transfer_retry_count: int = 3
    max_device_connections: int = 5


@dataclass
class GlobalSettings:
    """グローバル設定"""
    default_source: str = ""
    default_destination: str = ""
    hash_algorithm: str = "sha256"
    cache_hashes: bool = True
    max_concurrent_operations: int = 4
    buffer_size: int = 65536
    device_settings: DeviceSettings = field(default_factory=DeviceSettings)


@dataclass
class Preset:
    """プリセット設定"""
    name: str
    source: Optional[str] = None
    destination: str = ""
    folder_structure: FolderStructure = field(default_factory=FolderStructure)
    file_name_pattern: FileNamePattern = field(default_factory=FileNamePattern)
    duplicate_handling: DuplicateHandling = DuplicateHandling.RENAME
    include_associated_files: bool = True
    associated_file_rules: AssociatedFileRules = field(default_factory=AssociatedFileRules)
    log_level: str = "info"


@dataclass
class AppConfig:
    """アプリケーション設定"""
    version: str = "1.0"
    presets: List[Preset] = field(default_factory=list)
    global_settings: GlobalSettings = field(default_factory=GlobalSettings)
    device_profiles: List[DeviceProfile] = field(default_factory=list)
    
    def __post_init__(self):
        """初期化後処理"""
        if not self.device_profiles:
            self.device_profiles = self._create_default_device_profiles()
    
    def _create_default_device_profiles(self) -> List[DeviceProfile]:
        """デフォルトのデバイスプロファイルを作成"""
        return [
            DeviceProfile(
                device_id_pattern=r"com\.apple\.iPhone\.*",
                device_type=DeviceType.IOS,
                display_name="iPhone",
                icon="phone",
                default_paths=["/DCIM", "/PhotoData"],
                supported_formats=["jpg", "jpeg", "heic", "mov", "mp4", "m4v"],
                requires_authentication=True,
                transfer_protocol=TransferProtocol.AFC
            ),
            DeviceProfile(
                device_id_pattern=r"android\.*",
                device_type=DeviceType.ANDROID,
                display_name="Android Device",
                icon="phone-android",
                default_paths=["/DCIM/Camera", "/Pictures", "/Movies"],
                supported_formats=["jpg", "jpeg", "png", "mp4", "3gp", "webm"],
                requires_authentication=False,
                transfer_protocol=TransferProtocol.MTP
            ),
            DeviceProfile(
                device_id_pattern=r"camera\.*",
                device_type=DeviceType.CAMERA,
                display_name="Digital Camera",
                icon="camera",
                default_paths=["/DCIM"],
                supported_formats=["jpg", "jpeg", "raw", "cr2", "nef", "arw", "mp4", "mov"],
                requires_authentication=False,
                transfer_protocol=TransferProtocol.PTP
            )
        ]


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: AppConfig = AppConfig()
        self._ensure_config_directory()
    
    def _get_default_config_path(self) -> Path:
        """デフォルト設定ファイルパスを取得"""
        import platform
        system = platform.system()
        
        if system == "Windows":
            config_dir = Path.home() / "AppData" / "Roaming" / "VideoChecker"
        elif system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "VideoChecker"
        else:  # Linux
            config_dir = Path.home() / ".config" / "video-checker"
        
        return config_dir / "config.json"
    
    def _ensure_config_directory(self):
        """設定ディレクトリが存在することを確認"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> AppConfig:
        """設定ファイルを読み込み"""
        if not self.config_path.exists():
            logger.info("設定ファイルが見つかりません。デフォルト設定を使用します")
            self.save_config()  # デフォルト設定を保存
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml':
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            self.config = self._dict_to_config(data)
            logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            return self.config
            
        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            logger.info("デフォルト設定を使用します")
            return self.config
    
    def save_config(self, config: Optional[AppConfig] = None):
        """設定ファイルを保存"""
        if config:
            self.config = config
        
        try:
            config_dict = self._config_to_dict(self.config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, ensure_ascii=False)
                else:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"設定ファイルを保存しました: {self.config_path}")
            
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")
            raise
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """辞書からAppConfigオブジェクトに変換"""
        try:
            # プリセット変換
            presets = []
            for preset_data in data.get('presets', []):
                preset = Preset(
                    name=preset_data['name'],
                    source=preset_data.get('source'),
                    destination=preset_data.get('destination', ''),
                    duplicate_handling=DuplicateHandling(preset_data.get('duplicateHandling', 'rename')),
                    include_associated_files=preset_data.get('includeAssociatedFiles', True),
                    log_level=preset_data.get('logLevel', 'info')
                )
                
                # フォルダ構造変換
                if 'folderStructure' in preset_data:
                    folder_data = preset_data['folderStructure']
                    levels = []
                    for level_data in folder_data.get('levels', []):
                        level = FolderLevel(
                            type=level_data['type'],
                            field=level_data.get('field'),
                            format=level_data.get('format'),
                            value=level_data.get('value')
                        )
                        levels.append(level)
                    
                    preset.folder_structure = FolderStructure(
                        levels=levels,
                        separator=folder_data.get('separator', '/')
                    )
                
                # ファイル名パターン変換
                if 'fileNamePattern' in preset_data:
                    pattern_data = preset_data['fileNamePattern']
                    components = []
                    for comp_data in pattern_data.get('components', []):
                        component = FileNameComponent(
                            type=comp_data['type'],
                            field=comp_data.get('field'),
                            format=comp_data.get('format'),
                            value=comp_data.get('value'),
                            include_extension=comp_data.get('includeExtension', False)
                        )
                        components.append(component)
                    
                    conflict_resolution = ConflictResolution()
                    if 'conflictResolution' in pattern_data:
                        cr_data = pattern_data['conflictResolution']
                        conflict_resolution = ConflictResolution(
                            type=ConflictResolutionType(cr_data.get('type', 'sequence')),
                            digits=cr_data.get('digits', 3),
                            position=cr_data.get('position', 'before_extension')
                        )
                    
                    preset.file_name_pattern = FileNamePattern(
                        components=components,
                        conflict_resolution=conflict_resolution
                    )
                
                # 関連ファイルルール変換
                if 'associatedFileRules' in preset_data:
                    rules_data = preset_data['associatedFileRules']
                    preset.associated_file_rules = AssociatedFileRules(
                        same_base_name=rules_data.get('sameBaseName', []),
                        video_to_image=rules_data.get('videoToImage', []),
                        custom_patterns=rules_data.get('customPatterns', [])
                    )
                
                presets.append(preset)
            
            # グローバル設定変換
            global_settings = GlobalSettings()
            if 'globalSettings' in data:
                gs_data = data['globalSettings']
                global_settings = GlobalSettings(
                    default_source=gs_data.get('defaultSource', ''),
                    default_destination=gs_data.get('defaultDestination', ''),
                    hash_algorithm=gs_data.get('hashAlgorithm', 'sha256'),
                    cache_hashes=gs_data.get('cacheHashes', True),
                    max_concurrent_operations=gs_data.get('maxConcurrentOperations', 4),
                    buffer_size=gs_data.get('bufferSize', 65536)
                )
                
                # デバイス設定変換
                if 'deviceSettings' in gs_data:
                    ds_data = gs_data['deviceSettings']
                    global_settings.device_settings = DeviceSettings(
                        auto_detect_devices=ds_data.get('autoDetectDevices', True),
                        enable_device_notifications=ds_data.get('enableDeviceNotifications', True),
                        connection_timeout=ds_data.get('connectionTimeout', 30),
                        transfer_retry_count=ds_data.get('transferRetryCount', 3),
                        max_device_connections=ds_data.get('maxDeviceConnections', 5)
                    )
            
            # デバイスプロファイル変換
            device_profiles = []
            for profile_data in data.get('deviceProfiles', []):
                profile = DeviceProfile(
                    device_id_pattern=profile_data['deviceId'],
                    device_type=DeviceType(profile_data['deviceType']),
                    display_name=profile_data['displayName'],
                    icon=profile_data['icon'],
                    default_paths=profile_data.get('defaultPaths', []),
                    supported_formats=profile_data.get('supportedFormats', []),
                    requires_authentication=profile_data.get('requiresAuthentication', False),
                    transfer_protocol=TransferProtocol(profile_data.get('transferProtocol', 'unknown'))
                )
                device_profiles.append(profile)
            
            return AppConfig(
                version=data.get('version', '1.0'),
                presets=presets,
                global_settings=global_settings,
                device_profiles=device_profiles
            )
            
        except Exception as e:
            logger.error(f"設定データ変換エラー: {e}")
            return AppConfig()  # デフォルト設定を返す
    
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """AppConfigオブジェクトから辞書に変換"""
        def enum_serializer(obj):
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # dataclassから辞書への変換（enumの値変換含む）
        config_dict = asdict(config)
        
        # enumの値を文字列に変換
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        return convert_enums(config_dict)
    
    def get_preset_by_name(self, name: str) -> Optional[Preset]:
        """名前でプリセットを取得"""
        for preset in self.config.presets:
            if preset.name == name:
                return preset
        return None
    
    def add_preset(self, preset: Preset):
        """プリセットを追加"""
        # 同名のプリセットがあれば削除
        self.config.presets = [p for p in self.config.presets if p.name != preset.name]
        self.config.presets.append(preset)
    
    def remove_preset(self, name: str) -> bool:
        """プリセットを削除"""
        original_count = len(self.config.presets)
        self.config.presets = [p for p in self.config.presets if p.name != name]
        return len(self.config.presets) < original_count
    
    def get_device_profile_for_device(self, device_info) -> Optional[DeviceProfile]:
        """デバイス情報に対応するプロファイルを取得"""
        for profile in self.config.device_profiles:
            if profile.matches_device(device_info):
                return profile
        return None
    
    def validate_config(self) -> List[str]:
        """設定の妥当性チェック"""
        errors = []
        
        # プリセット名の重複チェック
        preset_names = [preset.name for preset in self.config.presets]
        if len(preset_names) != len(set(preset_names)):
            errors.append("プリセット名に重複があります")
        
        # 必須フィールドのチェック
        for preset in self.config.presets:
            if not preset.name:
                errors.append("プリセット名が空です")
            if not preset.destination:
                errors.append(f"プリセット '{preset.name}' の出力先が設定されていません")
        
        return errors 