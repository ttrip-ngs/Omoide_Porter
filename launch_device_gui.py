#!/usr/bin/env python
"""
デバイス接続GUIを起動するランチャー
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 直接device_guiモジュールを実行
if __name__ == "__main__":
    try:
        # device_guiを直接インポート
        import gui.device_gui as device_gui
        device_gui.main()
    except ImportError as e:
        print(f"インポートエラー: {e}")
        print("必要な依存関係を確認してください:")
        print("- PySide6")
        print("依存関係をインストールする場合: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"実行エラー: {e}")
        sys.exit(1) 