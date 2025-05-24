"""
デバイス管理システム
USB接続されたデバイス（iPhone、Android、カメラ等）の検出・管理を行う
"""

import logging
import platform
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .models import ConnectionStatus, DeviceInfo, DeviceType, TransferProtocol

logger = logging.getLogger(__name__)


class DeviceDetector(ABC):
    """デバイス検出器の抽象基底クラス"""

    @abstractmethod
    def detect_devices(self) -> List[DeviceInfo]:
        """接続されたデバイスを検出"""
        pass

    @abstractmethod
    def get_device_info(self, device_path: str) -> Optional[DeviceInfo]:
        """特定デバイスの詳細情報を取得"""
        pass


class WindowsDeviceDetector(DeviceDetector):
    """Windows用デバイス検出器"""

    def detect_devices(self) -> List[DeviceInfo]:
        """Windowsシステムでデバイスを検出"""
        devices = []

        try:
            # MTPデバイスの検出
            devices.extend(self._detect_mtp_devices())

            # Mass Storageデバイスの検出
            devices.extend(self._detect_mass_storage_devices())

            # iOSデバイスの検出
            devices.extend(self._detect_ios_devices())

        except Exception as e:
            logger.error(f"Windowsデバイス検出エラー: {e}")

        return devices

    def _detect_mtp_devices(self) -> List[DeviceInfo]:
        """MTPデバイス（Android等）を検出"""
        devices = []

        try:
            # WMI を使用してMTPデバイスを検出
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Service -eq "WpdUsb"} | Select-Object Name, DeviceID',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[2:]:  # ヘッダーをスキップ
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            device_name = " ".join(parts[:-1])
                            device_id = parts[-1]

                            device = DeviceInfo(
                                device_id=device_id,
                                device_type=DeviceType.ANDROID,
                                display_name=device_name,
                                protocol=TransferProtocol.MTP,
                                connection_status=ConnectionStatus.CONNECTED,
                            )
                            devices.append(device)

        except subprocess.TimeoutExpired:
            logger.warning("MTPデバイス検出がタイムアウトしました")
        except Exception as e:
            logger.error(f"MTPデバイス検出エラー: {e}")

        return devices

    def _detect_mass_storage_devices(self) -> List[DeviceInfo]:
        """Mass Storageデバイス（カメラ等）を検出"""
        devices = []

        try:
            # リムーバブルドライブを検出
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DriveType -eq 2} | Select-Object DeviceID, VolumeName, Size, FreeSpace",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[2:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 1:
                            drive_letter = parts[0]
                            volume_name = (
                                parts[1] if len(parts) > 1 else "Removable Drive"
                            )

                            # DCIMフォルダの存在をチェック
                            dcim_path = Path(f"{drive_letter}\\DCIM")
                            if dcim_path.exists():
                                device = DeviceInfo(
                                    device_id=f"msc_{drive_letter.replace(':', '')}",
                                    device_type=DeviceType.CAMERA,
                                    display_name=f"Camera ({volume_name})",
                                    protocol=TransferProtocol.MSC,
                                    connection_path=drive_letter,
                                    connection_status=ConnectionStatus.CONNECTED,
                                    available_paths=[str(dcim_path)],
                                )

                                # 容量情報を取得
                                try:
                                    if len(parts) >= 4:
                                        device.total_capacity = (
                                            int(parts[2]) if parts[2].isdigit() else 0
                                        )
                                        device.free_space = (
                                            int(parts[3]) if parts[3].isdigit() else 0
                                        )
                                except (ValueError, IndexError):
                                    pass

                                devices.append(device)

        except subprocess.TimeoutExpired:
            logger.warning("Mass Storageデバイス検出がタイムアウトしました")
        except Exception as e:
            logger.error(f"Mass Storageデバイス検出エラー: {e}")

        return devices

    def _detect_ios_devices(self) -> List[DeviceInfo]:
        """iOSデバイスを検出"""
        devices = []

        try:
            # pymobiledevice3を使用してiOSデバイスを検出
            # Note: 実際の実装では pymobiledevice3 ライブラリを使用
            # ここでは基本的な検出ロジックのみ実装

            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    'Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like "*Apple Mobile Device*" -or $_.Name -like "*iPhone*" -or $_.Name -like "*iPad*"} | Select-Object Name, DeviceID',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[2:]:
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            device_name = " ".join(parts[:-1])
                            device_id = parts[-1]

                            device = DeviceInfo(
                                device_id=device_id,
                                device_type=DeviceType.IOS,
                                display_name=device_name,
                                manufacturer="Apple",
                                protocol=TransferProtocol.AFC,
                                connection_status=ConnectionStatus.CONNECTED,
                            )
                            devices.append(device)

        except subprocess.TimeoutExpired:
            logger.warning("iOSデバイス検出がタイムアウトしました")
        except Exception as e:
            logger.error(f"iOSデバイス検出エラー: {e}")

        return devices

    def get_device_info(self, device_path: str) -> Optional[DeviceInfo]:
        """特定デバイスの詳細情報を取得"""
        # 実装予定
        return None


class MacOSDeviceDetector(DeviceDetector):
    """macOS用デバイス検出器"""

    def detect_devices(self) -> List[DeviceInfo]:
        """macOSシステムでデバイスを検出"""
        devices = []

        try:
            # system_profilerを使用してUSBデバイスを検出
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                devices.extend(self._parse_macos_usb_data(data))

        except subprocess.TimeoutExpired:
            logger.warning("macOSデバイス検出がタイムアウトしました")
        except Exception as e:
            logger.error(f"macOSデバイス検出エラー: {e}")

        return devices

    def _parse_macos_usb_data(self, usb_data: Dict) -> List[DeviceInfo]:
        """macOSのUSBデータを解析"""
        devices = []

        def parse_usb_items(items):
            for item in items:
                # iOSデバイスの検出
                if "Apple Inc." in item.get("manufacturer", "") and any(
                    keyword in item.get("_name", "").lower()
                    for keyword in ["iphone", "ipad"]
                ):

                    device = DeviceInfo(
                        device_id=item.get("serial_num", f"ios_{int(time.time())}"),
                        device_type=DeviceType.IOS,
                        display_name=item.get("_name", "iOS Device"),
                        manufacturer="Apple Inc.",
                        protocol=TransferProtocol.AFC,
                        connection_status=ConnectionStatus.CONNECTED,
                    )
                    devices.append(device)

                # Androidデバイスの検出
                elif "android" in item.get("_name", "").lower() or any(
                    keyword in item.get("manufacturer", "").lower()
                    for keyword in ["samsung", "google", "lg", "sony"]
                ):

                    device = DeviceInfo(
                        device_id=item.get("serial_num", f"android_{int(time.time())}"),
                        device_type=DeviceType.ANDROID,
                        display_name=item.get("_name", "Android Device"),
                        manufacturer=item.get("manufacturer", ""),
                        protocol=TransferProtocol.MTP,
                        connection_status=ConnectionStatus.CONNECTED,
                    )
                    devices.append(device)

                # 再帰的に子アイテムをチェック
                if "_items" in item:
                    parse_usb_items(item["_items"])

        if "SPUSBDataType" in usb_data:
            parse_usb_items(usb_data["SPUSBDataType"])

        return devices

    def get_device_info(self, device_path: str) -> Optional[DeviceInfo]:
        """特定デバイスの詳細情報を取得"""
        # 実装予定
        return None


class LinuxDeviceDetector(DeviceDetector):
    """Linux用デバイス検出器"""

    def detect_devices(self) -> List[DeviceInfo]:
        """Linuxシステムでデバイスを検出"""
        devices = []

        try:
            # lsusbを使用してUSBデバイスを検出
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                devices.extend(self._parse_linux_usb_data(result.stdout))

        except subprocess.TimeoutExpired:
            logger.warning("Linuxデバイス検出がタイムアウトしました")
        except Exception as e:
            logger.error(f"Linuxデバイス検出エラー: {e}")

        return devices

    def _parse_linux_usb_data(self, usb_output: str) -> List[DeviceInfo]:
        """LinuxのlsusbコマンドからUSBデータを解析"""
        devices = []

        for line in usb_output.strip().split("\n"):
            if not line.strip():
                continue

            # Apple製品の検出
            if "Apple, Inc." in line and any(
                keyword in line.lower() for keyword in ["iphone", "ipad"]
            ):
                device = DeviceInfo(
                    device_id=f"ios_{hash(line)}",
                    device_type=DeviceType.IOS,
                    display_name="iOS Device",
                    manufacturer="Apple Inc.",
                    protocol=TransferProtocol.AFC,
                    connection_status=ConnectionStatus.CONNECTED,
                )
                devices.append(device)

            # Androidデバイスの検出
            elif any(
                keyword in line.lower()
                for keyword in ["android", "samsung", "google", "lg"]
            ):
                device = DeviceInfo(
                    device_id=f"android_{hash(line)}",
                    device_type=DeviceType.ANDROID,
                    display_name="Android Device",
                    protocol=TransferProtocol.MTP,
                    connection_status=ConnectionStatus.CONNECTED,
                )
                devices.append(device)

        return devices

    def get_device_info(self, device_path: str) -> Optional[DeviceInfo]:
        """特定デバイスの詳細情報を取得"""
        # 実装予定
        return None


class DeviceManager:
    """デバイス管理クラス"""

    def __init__(self):
        self.detector = self._create_detector()
        self.connected_devices: Dict[str, DeviceInfo] = {}
        self.device_change_callbacks: List[Callable[[List[DeviceInfo]], None]] = []

    def _create_detector(self) -> DeviceDetector:
        """プラットフォームに応じたデバイス検出器を作成"""
        system = platform.system().lower()

        if system == "windows":
            return WindowsDeviceDetector()
        elif system == "darwin":
            return MacOSDeviceDetector()
        elif system == "linux":
            return LinuxDeviceDetector()
        else:
            logger.warning(f"未サポートのプラットフォーム: {system}")
            return WindowsDeviceDetector()  # フォールバック

    def scan_devices(self) -> List[DeviceInfo]:
        """接続されたデバイスをスキャン"""
        logger.info("デバイススキャンを開始")

        try:
            devices = self.detector.detect_devices()

            # デバイス情報を更新
            new_device_dict = {device.device_id: device for device in devices}

            # 変更があった場合はコールバックを呼び出し
            if new_device_dict != self.connected_devices:
                self.connected_devices = new_device_dict
                self._notify_device_change(devices)

            logger.info(f"{len(devices)}個のデバイスが見つかりました")
            return devices

        except Exception as e:
            logger.error(f"デバイススキャンエラー: {e}")
            return []

    def get_connected_devices(self) -> List[DeviceInfo]:
        """接続されているデバイス一覧を取得"""
        return list(self.connected_devices.values())

    def get_device_by_id(self, device_id: str) -> Optional[DeviceInfo]:
        """デバイスIDから特定のデバイスを取得"""
        return self.connected_devices.get(device_id)

    def add_device_change_callback(self, callback: Callable[[List[DeviceInfo]], None]):
        """デバイス変更時のコールバックを追加"""
        self.device_change_callbacks.append(callback)

    def remove_device_change_callback(
        self, callback: Callable[[List[DeviceInfo]], None]
    ):
        """デバイス変更時のコールバックを削除"""
        if callback in self.device_change_callbacks:
            self.device_change_callbacks.remove(callback)

    def _notify_device_change(self, devices: List[DeviceInfo]):
        """デバイス変更をコールバックに通知"""
        for callback in self.device_change_callbacks:
            try:
                callback(devices)
            except Exception as e:
                logger.error(f"デバイス変更コールバックエラー: {e}")

    def start_monitoring(self, interval: float = 5.0):
        """デバイス監視を開始（定期スキャン）"""
        import threading

        def monitor():
            while True:
                self.scan_devices()
                time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info(f"デバイス監視を開始しました（間隔: {interval}秒）")
