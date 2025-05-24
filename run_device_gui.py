#!/usr/bin/env python
"""
デバイス接続機能付きGUIアプリケーションのランチャー
"""

import sys
import os

# プロジェクトのルートディレクトリを追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# デバイス接続GUIを起動
from src.gui.device_gui import main

if __name__ == "__main__":
    main() 