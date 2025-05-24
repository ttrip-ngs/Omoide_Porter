#!/usr/bin/env python
"""
動画・写真コピーユーティリティ - メインアプリケーションランチャー
"""

import os
import sys

# プロジェクトのルートディレクトリを追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# メインウィンドウを起動
from src.gui.main_window import main

if __name__ == "__main__":
    main()
