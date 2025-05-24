#!/usr/bin/env python
"""
メインGUIのデバイス検出をテストするためのデバッグスクリプト
"""

import logging
import os
import sys

# ロギング設定（詳細レベル）
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# プロジェクトパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    print("=== メインGUIデバイス検出テスト ===")

    # デバイスマネージャーを個別にテスト
    from core.device_manager import DeviceManager

    print("\n1. DeviceManagerのテスト:")
    device_manager = DeviceManager()
    devices = device_manager.scan_devices()
    print(f"検出されたデバイス数: {len(devices)}")

    for i, device in enumerate(devices, 1):
        print(f"\n--- デバイス {i} ---")
        print(f"ID: {device.device_id}")
        print(f"名前: {device.display_name}")
        print(f"タイプ: {device.device_type.value}")
        print(f"接続状態: {device.connection_status.value}")
        print(f"利用可能パス: {device.available_paths}")

    # GUIを起動
    print("\n2. GUIの起動:")
    from PySide6.QtWidgets import QApplication

    from gui.main_window import ModernFileManagerWindow

    app = QApplication(sys.argv)

    # メインウィンドウを作成
    window = ModernFileManagerWindow()

    # デバイス情報を手動で設定してテスト
    print(f"GUI初期化完了。接続デバイス数: {len(window.connected_devices)}")

    # デバイス検出を手動実行
    print("\n3. GUI内でのデバイス検出テスト:")
    window._detect_devices()
    print(f"検出後のデバイス数: {len(window.connected_devices)}")

    window.show()
    print("\nGUIが表示されました。デバイス検出ボタンをテストしてください。")

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
