"""
コアデータモデル
設計書 docs/data_structure.md に基づくクラス定義
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class DeviceType(Enum):
    """デバイスタイプ列挙型"""

    IOS = "iOS"
    ANDROID = "Android"
    CAMERA = "Camera"
    UNKNOWN = "Unknown"


class ConnectionStatus(Enum):
    """接続状態列挙型"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTHENTICATING = "authenticating"
    AVAILABLE = "available"
    AUTHORIZATION_REQUIRED = "authorization_required"
    ERROR = "error"
    UNKNOWN = "unknown"


class TransferProtocol(Enum):
    """転送プロトコル列挙型"""

    AFC = "AFC"  # Apple File Conduit
    MTP = "MTP"  # Media Transfer Protocol
    PTP = "PTP"  # Picture Transfer Protocol
    MSC = "MSC"  # Mass Storage Class
    UNKNOWN = "unknown"


class FileStatus(Enum):
    """ファイル処理状態列挙型"""

    PENDING = "pending"
    COPYING = "copying"
    COPIED = "copied"
    SKIPPED = "skipped"
    ERROR = "error"
    DUPLICATE = "duplicate"


class SourceType(Enum):
    """ソースタイプ列挙型"""

    FOLDER = "folder"
    DEVICE = "device"


@dataclass
class DeviceInfo:
    """デバイス情報クラス"""

    # デバイス基本情報
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_type: DeviceType = DeviceType.UNKNOWN
    display_name: str = ""
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""

    # 接続情報
    protocol: TransferProtocol = TransferProtocol.UNKNOWN
    connection_path: str = ""
    is_authenticated: bool = False
    connection_status: ConnectionStatus = ConnectionStatus.UNKNOWN

    # ストレージ情報
    total_capacity: int = 0  # バイト
    free_space: int = 0  # バイト
    available_paths: List[str] = field(default_factory=list)

    # 転送情報
    transfer_speed: float = 0.0  # MB/s
    last_connected: Optional[datetime] = None

    def __post_init__(self):
        """初期化後処理"""
        if self.last_connected is None:
            self.last_connected = datetime.now()

    @property
    def capacity_gb(self) -> float:
        """容量をGBで取得"""
        return self.total_capacity / (1024**3) if self.total_capacity > 0 else 0.0

    @property
    def free_space_gb(self) -> float:
        """空き容量をGBで取得"""
        return self.free_space / (1024**3) if self.free_space > 0 else 0.0

    @property
    def used_space_percent(self) -> float:
        """使用容量の割合を取得"""
        if self.total_capacity <= 0:
            return 0.0
        used = self.total_capacity - self.free_space
        return (used / self.total_capacity) * 100

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "display_name": self.display_name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "protocol": self.protocol.value,
            "connection_path": self.connection_path,
            "is_authenticated": self.is_authenticated,
            "connection_status": self.connection_status.value,
            "total_capacity": self.total_capacity,
            "free_space": self.free_space,
            "available_paths": self.available_paths,
            "transfer_speed": self.transfer_speed,
            "last_connected": (
                self.last_connected.isoformat() if self.last_connected else None
            ),
        }


@dataclass
class FileInfo:
    """ファイル情報クラス"""

    # 元ファイル情報
    original_path: str = ""
    original_filename: str = ""
    original_basename: str = ""
    original_extension: str = ""
    size: int = 0
    last_modified: Optional[datetime] = None

    # ソース情報
    source_type: SourceType = SourceType.FOLDER
    source_device: Optional[DeviceInfo] = None

    # メディア情報
    media_type: str = "unknown"  # video, image, audio, document, unknown
    mime_type: str = ""

    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 処理結果
    hash: str = ""
    target_path: str = ""
    target_filename: str = ""
    status: FileStatus = FileStatus.PENDING
    error_message: str = ""

    # 関連ファイル
    associated_files: List["FileInfo"] = field(default_factory=list)
    is_associated_file: bool = False
    parent_file: Optional["FileInfo"] = None

    def __post_init__(self):
        """初期化後処理"""
        if self.original_path:
            path = Path(self.original_path)
            if not self.original_filename:
                self.original_filename = path.name
            if not self.original_basename:
                self.original_basename = path.stem
            if not self.original_extension:
                self.original_extension = path.suffix

    @property
    def size_mb(self) -> float:
        """ファイルサイズをMBで取得"""
        return self.size / (1024**2) if self.size > 0 else 0.0

    @property
    def size_human_readable(self) -> str:
        """人間が読みやすい形式でファイルサイズを取得"""
        if self.size == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(self.size)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    @property
    def is_image(self) -> bool:
        """画像ファイルかどうか"""
        return self.media_type == "image"

    @property
    def is_video(self) -> bool:
        """動画ファイルかどうか"""
        return self.media_type == "video"

    @property
    def is_raw(self) -> bool:
        """RAWファイルかどうか"""
        raw_extensions = {".raw", ".cr2", ".nef", ".arw", ".dng", ".orf", ".rw2"}
        return self.original_extension.lower() in raw_extensions

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """メタデータから値を取得"""
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """メタデータに値を設定"""
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "original_path": self.original_path,
            "original_filename": self.original_filename,
            "original_basename": self.original_basename,
            "original_extension": self.original_extension,
            "size": self.size,
            "last_modified": (
                self.last_modified.isoformat() if self.last_modified else None
            ),
            "source_type": self.source_type.value,
            "source_device": (
                self.source_device.to_dict() if self.source_device else None
            ),
            "media_type": self.media_type,
            "mime_type": self.mime_type,
            "metadata": self.metadata,
            "hash": self.hash,
            "target_path": self.target_path,
            "target_filename": self.target_filename,
            "status": self.status.value,
            "error_message": self.error_message,
            "is_associated_file": self.is_associated_file,
        }


@dataclass
class DeviceProfile:
    """デバイスプロファイル設定"""

    device_id_pattern: str
    device_type: DeviceType
    display_name: str
    icon: str
    default_paths: List[str] = field(default_factory=list)
    supported_formats: List[str] = field(default_factory=list)
    requires_authentication: bool = False
    transfer_protocol: TransferProtocol = TransferProtocol.UNKNOWN

    def matches_device(self, device_info: DeviceInfo) -> bool:
        """デバイスがこのプロファイルにマッチするかチェック"""
        import re

        try:
            return bool(re.match(self.device_id_pattern, device_info.device_id))
        except re.error:
            return False
