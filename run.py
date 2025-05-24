#!/usr/bin/env python
"""
動画・写真コピーユーティリティ実行ファイル
"""

import sys
import os

# プロジェクトルートをsys.pathに追加し、srcパッケージを見つけられるようにする
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
