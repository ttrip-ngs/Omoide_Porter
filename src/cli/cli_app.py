#!/usr/bin/env python
"""
動画・写真コピーユーティリティのCLIアプリケーション
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional

# 親ディレクトリをパスに追加して相対インポートを可能にする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_info import FileInfo
from core.metadata_extractor import MetadataExtractor
from core.path_generator import PathGenerator
from core.config_manager import ConfigManager
from core.file_operations import FileOperations
from core.filter_base import FilterChain
from core.filters import create_filter_chain_from_config


def setup_logging(log_level: str) -> None:
    """ロギングを設定"""
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }
    
    level = level_map.get(log_level.lower(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("video_copy_tool.log")
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="動画・写真ファイルを整理してコピーするツール"
    )
    
    parser.add_argument(
        "--source", "-s", 
        help="コピー元フォルダのパス"
    )
    
    parser.add_argument(
        "--destination", "-d", 
        help="コピー先のルートフォルダパス"
    )
    
    parser.add_argument(
        "--preset", "-p", 
        help="使用するプリセット名"
    )
    
    parser.add_argument(
        "--config", "-c", 
        help="設定ファイルのパス"
    )
    
    parser.add_argument(
        "--folder-structure", 
        help="フォルダ構造の定義（JSONフォーマット）"
    )
    
    parser.add_argument(
        "--filename-pattern", 
        help="ファイル名のパターン（JSONフォーマット）"
    )
    
    parser.add_argument(
        "--duplicate-handling", 
        choices=["skip", "overwrite", "rename", "ask"],
        default="rename",
        help="重複ファイルの処理方法"
    )
    
    # フィルタ関連オプション
    parser.add_argument(
        "--exclude-screenshots", 
        action="store_true",
        help="スクリーンショットファイルを除外"
    )
    
    parser.add_argument(
        "--include-media-types", 
        nargs="+",
        choices=["image", "video", "audio", "raw", "unknown"],
        help="含めるメディアタイプを指定"
    )
    
    parser.add_argument(
        "--exclude-media-types", 
        nargs="+",
        choices=["image", "video", "audio", "raw", "unknown"],
        help="除外するメディアタイプを指定"
    )
    
    parser.add_argument(
        "--min-file-size", 
        type=int,
        help="最小ファイルサイズ（バイト）"
    )
    
    parser.add_argument(
        "--max-file-size", 
        type=int,
        help="最大ファイルサイズ（バイト）"
    )
    
    parser.add_argument(
        "--source-device", 
        choices=["iOS", "Android", "Camera"],
        help="ソースデバイスタイプを指定（スクリーンショット判定に使用）"
    )
    
    parser.add_argument(
        "--log-level", 
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="ログレベル"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="実際にファイルをコピーせずシミュレーション実行"
    )
    
    parser.add_argument(
        "--yes", "-y", 
        action="store_true",
        help="すべての確認プロンプトにYesと答える"
    )
    
    parser.add_argument(
        "--recursive", "-r", 
        action="store_true",
        default=True,
        help="サブディレクトリも含めて処理"
    )
    
    parser.add_argument(
        "--show-filter-stats", 
        action="store_true",
        help="詳細なフィルタ統計を表示"
    )
    
    return parser.parse_args()


def create_filter_chain_from_args(args: argparse.Namespace) -> Optional[FilterChain]:
    """コマンドライン引数からFilterChainを作成"""
    # フィルタ関連の引数がない場合はNoneを返す
    if not any([
        args.exclude_screenshots,
        args.include_media_types,
        args.exclude_media_types,
        args.min_file_size,
        args.max_file_size
    ]):
        return None
    
    # 新しいフィルター設定形式に変換
    filters_config = {}
    
    # メディアタイプフィルター
    if args.include_media_types or args.exclude_media_types:
        filters_config["media_type"] = {
            "enabled": True,
            "priority": 10,
            "includeTypes": args.include_media_types or [],
            "excludeTypes": args.exclude_media_types or []
        }
    
    # スクリーンショットフィルター
    if args.exclude_screenshots:
        filters_config["screenshot"] = {
            "enabled": True,
            "priority": 50,
            "excludeScreenshots": True,
            "deviceType": args.source_device or "auto",
            "detection": {
                "enableFilenamePattern": True,
                "enablePathPattern": True,
                "enableMetadataPattern": True,
                "enableResolutionDetection": True,
                "customPatterns": []
            }
        }
    
    # ファイルサイズフィルター（未実装の場合は基本設定として保持）
    if args.min_file_size or args.max_file_size:
        # 将来的にFileSizeFilterを実装予定
        logging.warning("File size filtering not yet implemented in new filter system")
    
    if not filters_config:
        return None
    
    return create_filter_chain_from_config(filters_config)


def main():
    """メイン関数"""
    args = parse_arguments()
    
    # ロギング設定
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 設定ファイルの読み込み
    config_manager = ConfigManager()
    
    try:
        if args.config:
            settings = config_manager.load_config(args.config)
        elif args.preset:
            settings = config_manager.get_preset(args.preset)
        else:
            # デフォルト設定を作成
            settings = {
                "source": args.source,
                "destination": args.destination,
                "folderStructure": {"levels": [{"type": "literal", "value": "photos"}]},
                "fileNamePattern": {"components": [{"type": "original_filename"}]},
                "duplicateHandling": args.duplicate_handling,
                "hashAlgorithm": "sha256",
                "associatedFileExtensions": ["xmp", "thm", "aae"],
                "includeAssociatedFiles": True
            }
        
        # コマンドライン引数で設定をオーバーライド
        if args.source:
            settings["source"] = args.source
        if args.destination:
            settings["destination"] = args.destination
        if args.duplicate_handling:
            settings["duplicateHandling"] = args.duplicate_handling
        
        # 新しいFilterChainを作成
        filter_chain = None
        if "filters" in settings:
            # 設定ファイルからフィルターチェーンを作成
            filter_chain = create_filter_chain_from_config(settings["filters"])
        else:
            # コマンドライン引数からフィルターチェーンを作成
            filter_chain = create_filter_chain_from_args(args)
        
        if filter_chain:
            logger.info(f"Filter chain created: {filter_chain.get_filter_summary()}")
        
        # コピー処理を実行
        copy_process(settings, args.dry_run, args.yes, filter_chain, args.source_device, args.show_filter_stats)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


def copy_process(
    settings: Dict[str, Any], 
    dry_run: bool, 
    auto_yes: bool, 
    filter_chain: Optional[FilterChain] = None,
    source_device: Optional[str] = None,
    show_filter_stats: bool = False
) -> None:
    """コピー処理を実行"""
    source_dir = settings["source"]
    destination_root = settings["destination"]
    
    logging.info(f"コピー元: {source_dir}")
    logging.info(f"コピー先: {destination_root}")
    
    # フォルダ構造とファイル名パターンの要素を生成
    folder_elements = PathGenerator.parse_folder_structure(settings["folderStructure"])
    filename_elements = PathGenerator.parse_filename_pattern(settings["fileNamePattern"])
    
    duplicate_handling = settings.get("duplicateHandling", "rename")
    hash_algorithm = settings.get("hashAlgorithm", "sha256")
    associated_file_extensions = settings.get("associatedFileExtensions", 
                                             ["xmp", "thm", "aae"])
    
    if not os.path.exists(source_dir):
        logging.error(f"コピー元フォルダが存在しません: {source_dir}")
        sys.exit(1)
    
    # ファイルのスキャン（新しいフィルターチェーン使用）
    logging.info("ファイルをスキャン中...")
    
    # まず全ファイルをスキャン
    all_files = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_info = FileInfo(file_path, source_device)
            all_files.append(file_info)
    
    # メタデータを先に抽出（フィルタリングで必要になるため）
    logging.info("メタデータを抽出中...")
    for file_info in all_files:
        try:
            MetadataExtractor.extract_metadata(file_info)
        except Exception as e:
            logging.error(f"Failed to extract metadata: {str(e)}")
    
    # フィルターチェーンでファイルをフィルタリング
    file_info_list = []
    if filter_chain:
        for file_info in all_files:
            include, reason, metadata = filter_chain.should_include_file(file_info)
            if include:
                file_info_list.append(file_info)
        
        # フィルター統計を表示
        if show_filter_stats:
            stats = filter_chain.get_filter_summary()
            logging.info(f"=== フィルター統計 ===")
            for filter_info in stats['active_filters']:
                logging.info(f"  {filter_info['name']} (priority: {filter_info['priority']})")
            
            filter_stats = stats['stats']
            logging.info(f"総ファイル数: {filter_stats['total_files']}")
            logging.info(f"処理対象ファイル数: {filter_stats['included_files']}")
            logging.info(f"除外ファイル数: {filter_stats['excluded_files']}")
            logging.info(f"処理率: {filter_stats['inclusion_rate']:.1%}")
            
            if filter_stats['excluded_files'] > 0:
                logging.info(f"=== フィルター別除外詳細 ===")
                for filter_id, count in filter_stats['exclusion_by_filter'].items():
                    logging.info(f"  {filter_id}: {count}ファイル")
    else:
        file_info_list = all_files
    
    logging.info(f"{len(file_info_list)}ファイルを処理対象として選択しました")
    
    if not file_info_list:
        logging.warning("処理するファイルがありません")
        return
    
    # 関連ファイルの検索
    logging.info("関連ファイルを検索中...")
    associations = FileOperations.find_associated_files(
        file_info_list, associated_file_extensions
    )
    logging.info(f"{sum(len(v) for v in associations.values())}の関連ファイルを見つけました")
    
    # ターゲットパスの生成
    logging.info("コピー先パスを生成中...")
    FileOperations.generate_target_paths(
        file_info_list, folder_elements, filename_elements, destination_root
    )
    
    # パスの衝突を解決
    logging.info("パスの衝突を解決中...")
    FileOperations.resolve_path_conflicts(file_info_list, duplicate_handling)
    
    # 重複チェック
    logging.info("重複ファイルをチェック中...")
    duplicates = FileOperations.check_duplicates(file_info_list, hash_algorithm)
    
    if duplicates:
        logging.info(f"{len(duplicates)}のハッシュ値で重複が見つかりました")
    
    # 操作のプレビュー表示
    preview_copy_operations(file_info_list)
    
    # ドライラン時はここで終了
    if dry_run:
        logging.info("ドライランモード: 実際のコピーは行いません")
        return
    
    # ファイルのコピー前に確認
    if not auto_yes:
        confirm = input("ファイルをコピーしますか？ (y/n): ").lower().strip()
        if confirm != 'y' and confirm != 'yes':
            logging.info("操作がキャンセルされました")
            return
    
    # ファイルのコピー
    logging.info("ファイルをコピー中...")
    success_count = FileOperations.copy_files(file_info_list, progress_callback=show_progress)
    
    logging.info(f"コピー完了: {success_count}ファイルが正常にコピーされました")
    
    # エラーがあれば表示
    error_files = [f for f in file_info_list if f.status == "error"]
    if error_files:
        logging.warning(f"{len(error_files)}ファイルのコピーに失敗しました")
        for f in error_files:
            logging.error(f"エラー: {f.original_filename}: {f.error_message}")


def preview_copy_operations(file_info_list: List[FileInfo]) -> None:
    """コピー操作のプレビューを表示"""
    total = len(file_info_list)
    pending = sum(1 for f in file_info_list if f.status == "pending")
    skipped = sum(1 for f in file_info_list if f.status == "skipped")
    error = sum(1 for f in file_info_list if f.status == "error")
    
    print("\nコピー操作プレビュー:")
    print(f"  - 総ファイル数: {total}")
    print(f"  - コピー予定: {pending}")
    print(f"  - スキップ予定: {skipped}")
    print(f"  - エラー: {error}")
    
    # サンプルとして最初の数ファイルの詳細を表示
    max_preview = 5
    print("\n処理予定ファイルのサンプル:")
    
    sample_count = 0
    for file_info in file_info_list:
        if file_info.status == "pending" and sample_count < max_preview:
            print(f"  - {file_info.original_filename} -> {file_info.target_path}")
            sample_count += 1
    
    if pending > max_preview:
        print(f"  ... および他 {pending - max_preview} ファイル")
    
    print("")


def show_progress(current: int, total: int, current_file: str) -> None:
    """進捗状況を表示"""
    pct = int(current / total * 100) if total > 0 else 0
    bar_length = 30
    filled_length = int(bar_length * current / total) if total > 0 else 0
    
    bar = '=' * filled_length + '-' * (bar_length - filled_length)
    
    sys.stdout.write(f'\r[{bar}] {pct}% {current}/{total} {current_file}')
    sys.stdout.flush()
    
    if current == total:
        sys.stdout.write('\n')


if __name__ == "__main__":
    main() 