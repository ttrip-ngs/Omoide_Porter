#!/usr/bin/env python
"""
デバイス検出のデバッグスクリプト
"""

import logging
import os
import sys

# ロギング設定
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

# プロジェクトパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from core.device_manager import DeviceManager

    print("=== デバイス検出デバッグ ===")

    # DeviceManagerインスタンス作成
    device_manager = DeviceManager()
    print(f"検出器タイプ: {type(device_manager.detector).__name__}")

    # デバイススキャン実行
    print("\nデバイススキャン開始...")
    devices = device_manager.scan_devices()

    print(f"\n検出されたデバイス数: {len(devices)}")

    if devices:
        for i, device in enumerate(devices, 1):
            print(f"\n--- デバイス {i} ---")
            print(f"ID: {device.device_id}")
            print(f"名前: {device.display_name}")
            print(f"タイプ: {device.device_type.value}")
            print(f"メーカー: {device.manufacturer}")
            print(f"プロトコル: {device.protocol.value}")
            print(f"接続状態: {device.connection_status.value}")
            if device.available_paths:
                print(f"利用可能パス: {device.available_paths}")
    else:
        print("\nデバイスが見つかりませんでした。")

        # 手動でPowerShellコマンドをテスト
        print("\n=== PowerShellコマンドテスト ===")
        import subprocess

        # MTPデバイスチェック
        print("\n1. MTPデバイス検出テスト:")
        try:
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
            print(f"戻り値: {result.returncode}")
            print(f"出力: {result.stdout}")
            if result.stderr:
                print(f"エラー: {result.stderr}")
        except Exception as e:
            print(f"MTPテストエラー: {e}")

        # リムーバブルドライブチェック
        print("\n2. リムーバブルドライブ検出テスト:")
        try:
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
            print(f"戻り値: {result.returncode}")
            print(f"出力: {result.stdout}")
            if result.stderr:
                print(f"エラー: {result.stderr}")
        except Exception as e:
            print(f"リムーバブルドライブテストエラー: {e}")

        # iOSデバイスチェック
        print("\n3. iOSデバイス検出テスト:")
        try:
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
            print(f"戻り値: {result.returncode}")
            print(f"出力: {result.stdout}")
            if result.stderr:
                print(f"エラー: {result.stderr}")
        except Exception as e:
            print(f"iOSテストエラー: {e}")

except ImportError as e:
    print(f"インポートエラー: {e}")
except Exception as e:
    print(f"実行エラー: {e}")
    import traceback

    traceback.print_exc()
