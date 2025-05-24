#!/usr/bin/env python
"""
動画・写真コピーユーティリティ - コマンドラインインターフェース
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.device_manager import DeviceManager
from core.file_operations import FileOperations
from core.models import DeviceInfo, SourceType


class VideoPhotoToolCLI:
    """動画・写真コピーツールのCLIクラス"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.device_manager = DeviceManager()
        self.file_operations = FileOperations()
        self.logger = self._setup_logging()

        # 統計情報
        self.stats = {
            "files_processed": 0,
            "files_copied": 0,
            "files_skipped": 0,
            "files_error": 0,
            "bytes_processed": 0,
            "start_time": None,
            "end_time": None,
        }

    def _setup_logging(
        self, log_level: str = "INFO", log_file: Optional[str] = None
    ) -> logging.Logger:
        """ログ設定を初期化"""
        logger = logging.getLogger("video_photo_tool")
        logger.setLevel(getattr(logging, log_level.upper()))

        # 既存のハンドラーをクリア
        logger.handlers.clear()

        # フォーマッターを設定
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # ファイルハンドラー（指定された場合）
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def create_argument_parser(self) -> argparse.ArgumentParser:
        """コマンドライン引数パーサーを作成"""
        parser = argparse.ArgumentParser(
            description="動画・写真ファイルを整理してコピーするツール",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用例:
  # プリセットを使用してコピー
  python -m src.cli.main --preset "旅行写真" --source "/path/to/source" --destination "/path/to/dest"

  # デバイスからコピー
  python -m src.cli.main --device "iPhone" --destination "/path/to/dest"

  # ドライランでプレビュー
  python -m src.cli.main --preset "default" --source "/path/to/source" --destination "/path/to/dest" --dry-run

  # 設定ファイルを使用
  python -m src.cli.main --config "/path/to/config.json"
            """,
        )

        # ソース設定
        source_group = parser.add_mutually_exclusive_group()
        source_group.add_argument(
            "--source", "-s", type=str, help="コピー元のフォルダパス"
        )
        source_group.add_argument(
            "--device", "-d", type=str, help='デバイス名（例: "iPhone", "Android"）'
        )
        source_group.add_argument("--device-id", type=str, help="デバイスID")

        # コピー先設定
        parser.add_argument(
            "--destination", "-o", type=str, help="コピー先のフォルダパス"
        )

        # プリセット・設定
        config_group = parser.add_mutually_exclusive_group()
        config_group.add_argument(
            "--preset", "-p", type=str, help="使用するプリセット名"
        )
        config_group.add_argument(
            "--config", "-c", type=str, help="設定ファイルのパス（JSON/YAML）"
        )

        # フォルダ・ファイル名設定（プリセットを使わない場合）
        parser.add_argument(
            "--folder-structure",
            type=str,
            help='フォルダ構造パターン（例: "{撮影年}/{撮影月}/{撮影日}"）',
        )
        parser.add_argument(
            "--filename-pattern",
            type=str,
            help='ファイル名パターン（例: "{撮影年月日}_{時分秒}_{連番3桁}"）',
        )

        # 重複処理設定
        parser.add_argument(
            "--duplicate-handling",
            choices=["skip", "overwrite", "rename", "ask"],
            default="skip",
            help="重複ファイルの処理方法（デフォルト: skip）",
        )

        # フィルタ設定
        parser.add_argument(
            "--include-types",
            type=str,
            default="photo,video,raw",
            help="含めるファイル種別（カンマ区切り: photo,video,raw,other）",
        )
        parser.add_argument(
            "--exclude-extensions",
            type=str,
            help="除外する拡張子（カンマ区切り: .tmp,.log）",
        )
        parser.add_argument("--min-size", type=int, help="最小ファイルサイズ（MB）")
        parser.add_argument("--max-size", type=int, help="最大ファイルサイズ（MB）")

        # 処理オプション
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="実際のコピーは行わず、処理内容のプレビューを表示",
        )
        parser.add_argument(
            "--scan-only",
            action="store_true",
            help="ファイルスキャンのみ実行し、詳細情報を表示",
        )
        parser.add_argument(
            "--parallel", type=int, default=3, help="並列処理数（デフォルト: 3）"
        )
        parser.add_argument(
            "--no-hash", action="store_true", help="ハッシュ計算を無効にする"
        )
        parser.add_argument(
            "--no-metadata", action="store_true", help="メタデータ抽出を無効にする"
        )
        parser.add_argument(
            "--no-related", action="store_true", help="関連ファイルのコピーを無効にする"
        )

        # ログ・出力設定
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="ログレベル（デフォルト: INFO）",
        )
        parser.add_argument("--log-file", type=str, help="ログファイルのパス")
        parser.add_argument(
            "--progress",
            action="store_true",
            default=True,
            help="進捗バーを表示（デフォルト）",
        )
        parser.add_argument(
            "--no-progress", action="store_true", help="進捗バーを非表示"
        )
        parser.add_argument(
            "--quiet", "-q", action="store_true", help="最小限の出力のみ表示"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="詳細な出力を表示"
        )

        # 確認・検証
        parser.add_argument(
            "--yes",
            "-y",
            action="store_true",
            help="確認プロンプトを全て「はい」として自動応答",
        )
        parser.add_argument(
            "--validate-config",
            action="store_true",
            help="設定ファイルの妥当性をチェック",
        )

        # 情報表示
        parser.add_argument(
            "--list-presets",
            action="store_true",
            help="利用可能なプリセットの一覧を表示",
        )
        parser.add_argument(
            "--list-devices", action="store_true", help="接続されたデバイスの一覧を表示"
        )
        parser.add_argument(
            "--version",
            action="version",
            version="動画・写真コピーユーティリティ 1.0.0",
        )

        return parser

    async def execute_command(self, args: argparse.Namespace) -> int:
        """コマンドを実行"""
        try:
            # ログ設定を更新
            if args.log_file or args.log_level != "INFO":
                self.logger = self._setup_logging(args.log_level, args.log_file)

            # 静的な情報表示コマンド
            if args.list_presets:
                return self._list_presets()

            if args.list_devices:
                return await self._list_devices()

            if args.validate_config:
                return self._validate_config(args.config)

            # メイン処理
            if args.scan_only:
                return await self._scan_files(args)
            else:
                return await self._copy_files(args)

        except KeyboardInterrupt:
            self.logger.warning("処理が中断されました")
            return 130  # SIGINT
        except Exception as e:
            self.logger.error(f"エラーが発生しました: {str(e)}")
            if args.verbose:
                import traceback

                self.logger.error(traceback.format_exc())
            return 1

    def _list_presets(self) -> int:
        """利用可能なプリセット一覧を表示"""
        try:
            presets = self.config_manager.list_presets()

            if not presets:
                print("利用可能なプリセットがありません。")
                return 0

            print("利用可能なプリセット:")
            print("-" * 50)

            for preset_name in presets:
                try:
                    preset_data = self.config_manager.load_preset(preset_name)
                    description = preset_data.get("description", "説明なし")
                    print(f"  {preset_name}: {description}")
                except Exception as e:
                    print(f"  {preset_name}: エラー - {str(e)}")

            return 0

        except Exception as e:
            self.logger.error(f"プリセット一覧の取得に失敗しました: {str(e)}")
            return 1

    async def _list_devices(self) -> int:
        """接続されたデバイス一覧を表示"""
        try:
            print("デバイスを検索中...")
            devices = self.device_manager.get_connected_devices()

            if not devices:
                print("接続されたデバイスが見つかりません。")
                return 0

            print("接続されたデバイス:")
            print("-" * 60)

            for device in devices:
                status_icon = "✅" if device.status.value == "available" else "❌"
                print(f"  {status_icon} {device.name}")
                print(f"     タイプ: {device.device_type.value}")
                print(f"     ステータス: {device.status.value}")
                if device.available_paths:
                    print(f"     パス: {', '.join(device.available_paths)}")
                print()

            return 0

        except Exception as e:
            self.logger.error(f"デバイス一覧の取得に失敗しました: {str(e)}")
            return 1

    def _validate_config(self, config_path: Optional[str]) -> int:
        """設定ファイルの検証"""
        if not config_path:
            self.logger.error("設定ファイルのパスが指定されていません")
            return 2

        try:
            config_data = self.config_manager.load_config_file(config_path)

            # 設定の検証
            required_fields = ["folder_structure", "processing_options"]
            missing_fields = [
                field for field in required_fields if field not in config_data
            ]

            if missing_fields:
                self.logger.error(
                    f"必須フィールドが不足しています: {', '.join(missing_fields)}"
                )
                return 64

            print(f"設定ファイル '{config_path}' は有効です。")
            return 0

        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {config_path}")
            return 65
        except Exception as e:
            self.logger.error(f"設定ファイルの検証に失敗しました: {str(e)}")
            return 64

    async def _scan_files(self, args: argparse.Namespace) -> int:
        """ファイルスキャンのみ実行"""
        try:
            # ソースの決定
            source_path = await self._determine_source(args)
            if not source_path:
                return 1

            self.logger.info(f"ファイルスキャンを開始: {source_path}")
            self.stats["start_time"] = time.time()

            # ファイルスキャン
            files = self.file_operations.scan_directory(source_path, recursive=True)

            # フィルタ適用
            filtered_files = self._apply_filters(files, args)

            # 結果表示
            self._display_scan_results(filtered_files, args)

            self.stats["end_time"] = time.time()
            self._display_statistics()

            return 0

        except Exception as e:
            self.logger.error(f"ファイルスキャンに失敗しました: {str(e)}")
            return 1

    async def _copy_files(self, args: argparse.Namespace) -> int:
        """ファイルコピー処理を実行"""
        try:
            # 必須パラメータのチェック
            if not args.destination:
                self.logger.error("コピー先が指定されていません (--destination)")
                return 2

            # ソースの決定
            source_path = await self._determine_source(args)
            if not source_path:
                return 1

            # 設定の読み込み
            config = await self._load_configuration(args)

            # 確認プロンプト
            if not args.yes and not args.dry_run:
                if not self._confirm_operation(source_path, args.destination, config):
                    self.logger.info("処理がキャンセルされました")
                    return 0

            self.logger.info(f"処理を開始: {source_path} -> {args.destination}")
            self.stats["start_time"] = time.time()

            # ファイルスキャン
            files = self.file_operations.scan_directory(source_path, recursive=True)
            filtered_files = self._apply_filters(files, args)

            # コピー処理実行
            if args.dry_run:
                self._display_dry_run_results(filtered_files, args.destination, config)
            else:
                await self._execute_copy_operation(
                    filtered_files, args.destination, config, args
                )

            self.stats["end_time"] = time.time()
            self._display_statistics()

            # 終了コードの決定
            if self.stats["files_error"] > 0:
                return 3  # 一部エラー
            elif self.stats["files_skipped"] > 0:
                return 4  # 重複スキップあり
            else:
                return 0  # 正常終了

        except Exception as e:
            self.logger.error(f"コピー処理に失敗しました: {str(e)}")
            return 1

    async def _determine_source(self, args: argparse.Namespace) -> Optional[str]:
        """ソースパスを決定"""
        if args.source:
            if not os.path.exists(args.source):
                self.logger.error(f"ソースフォルダが存在しません: {args.source}")
                return None
            return args.source

        elif args.device or args.device_id:
            # デバイスからソースを取得
            devices = self.device_manager.get_connected_devices()

            target_device = None
            if args.device_id:
                target_device = next(
                    (d for d in devices if d.device_id == args.device_id), None
                )
            elif args.device:
                target_device = next(
                    (d for d in devices if args.device.lower() in d.name.lower()), None
                )

            if not target_device:
                self.logger.error(
                    f"指定されたデバイスが見つかりません: {args.device or args.device_id}"
                )
                return None

            if not target_device.available_paths:
                self.logger.error(
                    f"デバイスにアクセス可能なパスがありません: {target_device.name}"
                )
                return None

            # 最初の利用可能パスを使用
            return target_device.available_paths[0]

        else:
            self.logger.error(
                "ソースが指定されていません (--source, --device, --device-id のいずれかが必要)"
            )
            return None

    async def _load_configuration(self, args: argparse.Namespace) -> Dict:
        """設定を読み込み"""
        config = {}

        if args.config:
            # 設定ファイルから読み込み
            config = self.config_manager.load_config_file(args.config)
        elif args.preset:
            # プリセットから読み込み
            config = self.config_manager.load_preset(args.preset)
        else:
            # コマンドライン引数から構築
            config = {
                "folder_structure": {
                    "pattern": args.folder_structure or "{撮影年}/{撮影月}/{撮影日}"
                },
                "filename_rules": {
                    "enabled": bool(args.filename_pattern),
                    "pattern": args.filename_pattern or "{元のファイル名}",
                },
                "processing_options": {
                    "duplicate_handling": args.duplicate_handling,
                    "parallel_count": args.parallel,
                    "calculate_hash": not args.no_hash,
                    "extract_metadata": not args.no_metadata,
                    "copy_related": not args.no_related,
                },
            }

        return config

    def _apply_filters(self, files: List[str], args: argparse.Namespace) -> List[str]:
        """ファイルフィルタを適用"""
        filtered_files = []

        # ファイル種別フィルタ
        include_types = set(args.include_types.split(","))

        # 除外拡張子
        exclude_extensions = set()
        if args.exclude_extensions:
            exclude_extensions = set(args.exclude_extensions.split(","))

        for file_path in files:
            file_path_obj = Path(file_path)

            # 拡張子チェック
            if file_path_obj.suffix.lower() in exclude_extensions:
                continue

            # ファイル種別チェック
            file_type = self._determine_file_type(file_path)
            if file_type not in include_types:
                continue

            # サイズチェック
            try:
                file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
                if args.min_size and file_size_mb < args.min_size:
                    continue
                if args.max_size and file_size_mb > args.max_size:
                    continue
            except OSError:
                continue

            filtered_files.append(file_path)

        return filtered_files

    def _determine_file_type(self, file_path: str) -> str:
        """ファイル種別を判定"""
        ext = Path(file_path).suffix.lower()

        photo_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
        raw_extensions = {
            ".cr2",
            ".cr3",
            ".nef",
            ".arw",
            ".dng",
            ".raw",
            ".raf",
            ".orf",
        }

        if ext in photo_extensions:
            return "photo"
        elif ext in video_extensions:
            return "video"
        elif ext in raw_extensions:
            return "raw"
        else:
            return "other"

    def _confirm_operation(self, source: str, destination: str, config: Dict) -> bool:
        """操作の確認"""
        print("\n=== 処理内容の確認 ===")
        print(f"ソース: {source}")
        print(f"コピー先: {destination}")
        print(
            f"フォルダ構造: {config.get('folder_structure', {}).get('pattern', '未設定')}"
        )
        print(
            f"重複処理: {config.get('processing_options', {}).get('duplicate_handling', '未設定')}"
        )
        print()

        response = input("この内容で処理を実行しますか？ [y/N]: ").strip().lower()
        return response in ["y", "yes"]

    def _display_scan_results(self, files: List[str], args: argparse.Namespace):
        """スキャン結果を表示"""
        if not args.quiet:
            print(f"\n=== スキャン結果 ===")
            print(f"発見されたファイル数: {len(files)}")

            if args.verbose:
                # ファイル種別ごとの統計
                type_counts = {}
                total_size = 0

                for file_path in files:
                    file_type = self._determine_file_type(file_path)
                    type_counts[file_type] = type_counts.get(file_type, 0) + 1

                    try:
                        total_size += Path(file_path).stat().st_size
                    except OSError:
                        pass

                print("\nファイル種別:")
                for file_type, count in type_counts.items():
                    print(f"  {file_type}: {count}ファイル")

                print(f"\n合計サイズ: {self._format_size(total_size)}")

                if len(files) <= 20:  # 20ファイル以下の場合は一覧表示
                    print("\nファイル一覧:")
                    for file_path in files:
                        print(f"  {file_path}")

    def _display_dry_run_results(
        self, files: List[str], destination: str, config: Dict
    ):
        """ドライラン結果を表示"""
        print(f"\n=== ドライラン結果 ===")
        print(f"コピー対象ファイル数: {len(files)}")
        print(f"コピー先: {destination}")
        print()

        # サンプルファイルでプレビュー生成
        folder_pattern = config.get("folder_structure", {}).get(
            "pattern", "{撮影年}/{撮影月}/{撮影日}"
        )

        print("コピー先パスの例:")
        for i, file_path in enumerate(files[:5]):  # 最初の5ファイルのみ
            sample_dest = self._generate_destination_path(
                file_path, destination, config
            )
            print(f"  {Path(file_path).name} -> {sample_dest}")

        if len(files) > 5:
            print(f"  ... 他 {len(files) - 5} ファイル")

    async def _execute_copy_operation(
        self, files: List[str], destination: str, config: Dict, args: argparse.Namespace
    ):
        """コピー操作を実行"""
        if not args.quiet:
            print(f"\nコピー処理を開始します...")

        # 進捗バーの設定
        show_progress = args.progress and not args.no_progress and not args.quiet

        processed = 0
        for file_path in files:
            try:
                # コピー先パス生成
                dest_path = self._generate_destination_path(
                    file_path, destination, config
                )

                # ディレクトリ作成
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # ファイルコピー
                if self._should_copy_file(file_path, dest_path, config):
                    self._copy_file(file_path, dest_path)
                    self.stats["files_copied"] += 1
                    if args.verbose:
                        self.logger.info(f"コピー完了: {file_path} -> {dest_path}")
                else:
                    self.stats["files_skipped"] += 1
                    if args.verbose:
                        self.logger.info(f"スキップ: {file_path}")

                self.stats["files_processed"] += 1
                processed += 1

                # 進捗表示
                if show_progress:
                    self._display_progress(processed, len(files))

            except Exception as e:
                self.stats["files_error"] += 1
                self.logger.error(f"ファイル処理エラー: {file_path} - {str(e)}")

        if show_progress:
            print()  # 進捗バーの後に改行

    def _generate_destination_path(
        self, file_path: str, destination: str, config: Dict
    ) -> str:
        """コピー先パスを生成"""
        # 簡易的な実装（実際はメタデータを使用）
        file_path_obj = Path(file_path)
        folder_pattern = config.get("folder_structure", {}).get("pattern", "")

        # サンプル値でパターンを置換
        folder = folder_pattern.replace("{撮影年}", "2023")
        folder = folder.replace("{撮影月}", "10")
        folder = folder.replace("{撮影日}", "27")
        folder = folder.replace("{ファイル種別}", self._determine_file_type(file_path))

        filename = file_path_obj.name
        filename_rules = config.get("filename_rules", {})
        if filename_rules.get("enabled"):
            pattern = filename_rules.get("pattern", "{元のファイル名}")
            filename = pattern.replace("{元のファイル名}", file_path_obj.stem)
            filename += file_path_obj.suffix

        return os.path.join(destination, folder, filename)

    def _should_copy_file(self, source_path: str, dest_path: str, config: Dict) -> bool:
        """ファイルをコピーすべきかチェック"""
        if not os.path.exists(dest_path):
            return True

        duplicate_handling = config.get("processing_options", {}).get(
            "duplicate_handling", "skip"
        )

        if duplicate_handling == "skip":
            return False
        elif duplicate_handling == "overwrite":
            return True
        elif duplicate_handling == "rename":
            # 実際の実装では名前を変更
            return True
        else:  # ask
            response = input(
                f"ファイルが既に存在します: {dest_path}\n上書きしますか？ [y/N]: "
            )
            return response.lower() in ["y", "yes"]

    def _copy_file(self, source_path: str, dest_path: str):
        """ファイルをコピー"""
        import shutil

        shutil.copy2(source_path, dest_path)

        # ファイルサイズを統計に追加
        self.stats["bytes_processed"] += Path(source_path).stat().st_size

    def _display_progress(self, current: int, total: int):
        """進捗バーを表示"""
        if total == 0:
            return

        percentage = (current / total) * 100
        bar_length = 50
        filled_length = int(bar_length * current // total)

        bar = "█" * filled_length + "-" * (bar_length - filled_length)

        print(
            f"\r進捗: |{bar}| {current}/{total} ({percentage:.1f}%)", end="", flush=True
        )

    def _display_statistics(self):
        """統計情報を表示"""
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = self.stats["end_time"] - self.stats["start_time"]

            print(f"\n=== 処理統計 ===")
            print(f"処理時間: {duration:.2f}秒")
            print(f"処理ファイル数: {self.stats['files_processed']}")
            print(f"コピー成功: {self.stats['files_copied']}")
            print(f"スキップ: {self.stats['files_skipped']}")
            print(f"エラー: {self.stats['files_error']}")
            print(f"処理サイズ: {self._format_size(self.stats['bytes_processed'])}")

            if duration > 0:
                speed = self.stats["bytes_processed"] / duration / (1024 * 1024)
                print(f"処理速度: {speed:.2f} MB/s")

    def _format_size(self, size_bytes: int) -> str:
        """ファイルサイズをフォーマット"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


async def main():
    """メイン関数"""
    cli = VideoPhotoToolCLI()
    parser = cli.create_argument_parser()
    args = parser.parse_args()

    exit_code = await cli.execute_command(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
