#!/usr/bin/env python
"""
動画・写真コピーユーティリティのエントリーポイント
"""

import sys
import argparse


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="動画・写真ファイルを整理してコピーするツール"
    )
    
    parser.add_argument(
        "--gui", "-g", 
        action="store_true",
        help="GUIモードで起動"
    )
    
    args, remaining_args = parser.parse_known_args()
    
    # コマンドライン引数に基づいてモードを切り替え
    if args.gui:
        # GUIモード
        from .gui import main as gui_main
        gui_main()
    else:
        # CLIモード
        # CLIモードの場合は、sys.argvを適切に設定する必要があるため、
        # ここで相対インポートを行うと引数の扱いが複雑になる可能性がある。
        # run.pyでsrcをパスに追加しているので、
        # srcパッケージ内のモジュールとしてcliを直接インポートできるか試す。
        # それでも問題が解決しない場合は、python -m src ... の実行形式を推奨する。
        from src.cli import main as cli_main
        # オリジナルのsys.argvを復元し、__main__.pyに渡された引数のみをcliに渡す
        current_script_name = sys.argv[0] 
        sys.argv = [current_script_name] + remaining_args
        cli_main()


if __name__ == "__main__":
    main() 