#!/usr/bin/env python
"""
GUIのデバイス検出をテストするためのデバッグスクリプト
"""

import logging
import os
import sys

# ロギング設定
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# プロジェクトパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from core.device_manager import DeviceManager
    from core.models import DeviceType

    print("=== デバイス検出改良テスト ===")

    # DeviceManagerインスタンス作成
    device_manager = DeviceManager()

    # デバイススキャン実行
    print("\nデバイススキャン開始...")
    devices = device_manager.scan_devices()

    print(f"\n検出されたデバイス数: {len(devices)}")

    # iOSデバイスにパスを追加
    for device in devices:
        if device.device_type == DeviceType.IOS and not device.available_paths:
            device.available_paths = [
                "/DCIM",
                "/var/mobile/Media/DCIM",
                "/Media/PhotoData",
            ]
            print(f"iOSデバイス '{device.display_name}' にパスを追加しました")

    # GUIを起動
    print("\nGUIを起動しています...")

    from PySide6.QtWidgets import QApplication

    from gui.device_gui import DeviceConnectionWidget

    app = QApplication(sys.argv)

    # デバイス情報を事前に設定してGUIウィンドウを作成
    window = DeviceConnectionWidget()

    # 検出されたデバイスを手動でGUIに設定
    window.connected_devices = devices
    window._update_device_list()
    window._log_message(f"デバイス検出完了: {len(devices)}台発見")

    window.show()

    print("GUI起動完了。ウィンドウを確認してください。")

    sys.exit(app.exec())

except ImportError as e:
    print(f"インポートエラー: {e}")
    print("必要な依存関係:")
    print("- PySide6")
    print("pip install -r requirements.txt でインストールしてください")
except Exception as e:
    print(f"実行エラー: {e}")
    import traceback

    traceback.print_exc()
