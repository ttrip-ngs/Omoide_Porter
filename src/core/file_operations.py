import os
import shutil
import logging
from typing import List, Dict, Optional, Literal, Callable

from .file_info import FileInfo
from .metadata_extractor import MetadataExtractor
from .path_generator import PathElement, PathGenerator
from .file_filter import FileFilter, FilterStats
from .filter_base import FilterChain

logger = logging.getLogger(__name__)


class FileOperations:
    """ファイル操作を行うクラス"""
    
    @staticmethod
    def scan_directory(
        source_dir: str,
        recursive: bool = True,
        file_filter: Optional[FileFilter] = None,
        source_device: Optional[str] = None
    ) -> List[FileInfo]:
        """
        ディレクトリをスキャンしてファイル情報のリストを取得（旧フィルターシステム用）
        
        Args:
            source_dir: スキャン対象のディレクトリ
            recursive: サブディレクトリも再帰的にスキャンするかどうか
            file_filter: ファイルフィルタ（None の場合はフィルタリングしない）
            source_device: ソースデバイスタイプ (iOS, Android, Camera等)
            
        Returns:
            ファイル情報のリスト
        """
        file_info_list = []
        filter_stats = FilterStats() if file_filter else None
        
        if not os.path.exists(source_dir):
            logger.error(f"Source directory not found: {source_dir}")
            return file_info_list
        
        try:
            if recursive:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_info = FileInfo(file_path, source_device)
                        
                        # フィルタリング
                        if file_filter:
                            if file_filter.should_include_file(file_info):
                                file_info_list.append(file_info)
                                if filter_stats:
                                    filter_stats.add_file(True)
                            else:
                                if filter_stats:
                                    filter_stats.add_file(False, "filter")
                        else:
                            file_info_list.append(file_info)
            else:
                for file in os.listdir(source_dir):
                    file_path = os.path.join(source_dir, file)
                    if os.path.isfile(file_path):
                        file_info = FileInfo(file_path, source_device)
                        
                        # フィルタリング
                        if file_filter:
                            if file_filter.should_include_file(file_info):
                                file_info_list.append(file_info)
                                if filter_stats:
                                    filter_stats.add_file(True)
                            else:
                                if filter_stats:
                                    filter_stats.add_file(False, "filter")
                        else:
                            file_info_list.append(file_info)
        
        except Exception as e:
            logger.error(f"Error scanning directory {source_dir}: {str(e)}")
        
        # フィルタ統計をログ出力
        if filter_stats and file_filter and file_filter.enabled:
            stats = filter_stats.get_summary()
            logger.info(f"Filter results: {stats['included_files']}/{stats['total_files']} files included "
                       f"({stats['inclusion_rate']:.1%})")
            if stats['excluded_files'] > 0:
                breakdown = stats['exclusion_breakdown']
                excluded_details = []
                for reason, count in breakdown.items():
                    if count > 0:
                        excluded_details.append(f"{reason}: {count}")
                if excluded_details:
                    logger.info(f"Excluded files breakdown: {', '.join(excluded_details)}")
        
        return file_info_list
    
    @staticmethod
    def scan_directory_with_filter_chain(
        source_dir: str,
        recursive: bool = True,
        filter_chain: Optional[FilterChain] = None,
        source_device: Optional[str] = None,
        extract_metadata: bool = True
    ) -> List[FileInfo]:
        """
        ディレクトリをスキャンしてファイル情報のリストを取得（新フィルターシステム用）
        
        Args:
            source_dir: スキャン対象のディレクトリ
            recursive: サブディレクトリも再帰的にスキャンするかどうか
            filter_chain: フィルターチェーン（None の場合はフィルタリングしない）
            source_device: ソースデバイスタイプ (iOS, Android, Camera等)
            extract_metadata: メタデータを自動抽出するかどうか
            
        Returns:
            ファイル情報のリスト
        """
        if not os.path.exists(source_dir):
            logger.error(f"Source directory not found: {source_dir}")
            return []
        
        # すべてのファイルをスキャン
        all_files = []
        try:
            if recursive:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_info = FileInfo(file_path, source_device)
                        all_files.append(file_info)
            else:
                for file in os.listdir(source_dir):
                    file_path = os.path.join(source_dir, file)
                    if os.path.isfile(file_path):
                        file_info = FileInfo(file_path, source_device)
                        all_files.append(file_info)
        except Exception as e:
            logger.error(f"Error scanning directory {source_dir}: {str(e)}")
            return []
        
        # メタデータ抽出（フィルタリングで必要になる場合があるため）
        if extract_metadata:
            for file_info in all_files:
                try:
                    MetadataExtractor.extract_metadata(file_info)
                except Exception as e:
                    logger.error(f"Failed to extract metadata for {file_info.original_filename}: {str(e)}")
        
        # フィルターチェーンでフィルタリング
        if filter_chain:
            filtered_files = []
            for file_info in all_files:
                include, reason, metadata = filter_chain.should_include_file(file_info)
                if include:
                    filtered_files.append(file_info)
            
            return filtered_files
        else:
            return all_files
    
    @staticmethod
    def scan_directory_with_detailed_filtering(
        source_dir: str,
        recursive: bool = True,
        file_filter: Optional[FileFilter] = None,
        source_device: Optional[str] = None
    ) -> tuple[List[FileInfo], FilterStats]:
        """
        詳細なフィルタ統計付きでディレクトリをスキャン
        
        Args:
            source_dir: スキャン対象のディレクトリ
            recursive: サブディレクトリも再帰的にスキャンするかどうか
            file_filter: ファイルフィルタ
            source_device: ソースデバイスタイプ
            
        Returns:
            (ファイル情報のリスト, フィルタ統計)
        """
        file_info_list = []
        filter_stats = FilterStats()
        
        if not os.path.exists(source_dir):
            logger.error(f"Source directory not found: {source_dir}")
            return file_info_list, filter_stats
        
        try:
            for root, dirs, files in os.walk(source_dir) if recursive else [(source_dir, [], os.listdir(source_dir))]:
                for file in files:
                    if not recursive and not os.path.isfile(os.path.join(source_dir, file)):
                        continue
                    
                    file_path = os.path.join(root, file)
                    file_info = FileInfo(file_path, source_device)
                    
                    # 個別フィルタチェック（詳細統計用）
                    if file_filter and file_filter.enabled:
                        exclusion_reason = None
                        
                        # メディアタイプチェック
                        if not file_filter._check_media_type_filter(file_info):
                            exclusion_reason = "media_type"
                        # 拡張子チェック
                        elif not file_filter._check_extension_filter(file_info):
                            exclusion_reason = "extension"
                        # ファイルサイズチェック
                        elif not file_filter._check_size_filter(file_info):
                            exclusion_reason = "size"
                        # ファイル名パターンチェック
                        elif not file_filter._check_filename_filter(file_info):
                            exclusion_reason = "filename"
                        # パスパターンチェック
                        elif not file_filter._check_path_filter(file_info):
                            exclusion_reason = "path"
                        # スクリーンショットチェック
                        elif file_filter.exclude_screenshots and file_filter._is_screenshot_by_filter(file_info):
                            exclusion_reason = "screenshot"
                        
                        if exclusion_reason:
                            filter_stats.add_file(False, exclusion_reason)
                        else:
                            file_info_list.append(file_info)
                            filter_stats.add_file(True)
                    else:
                        file_info_list.append(file_info)
                        filter_stats.add_file(True)
        
        except Exception as e:
            logger.error(f"Error scanning directory {source_dir}: {str(e)}")
        
        return file_info_list, filter_stats
    
    @staticmethod
    def process_file_metadata(
        file_info_list: List[FileInfo],
        associated_file_extensions: Optional[List[str]] = None
    ) -> None:
        """
        ファイルリストのメタデータを処理
        
        Args:
            file_info_list: ファイル情報のリスト
            associated_file_extensions: 関連ファイルとみなす拡張子のリスト
        """
        # 関連ファイルの拡張子（デフォルト値）
        if associated_file_extensions is None:
            associated_file_extensions = ["xmp", "thm", "aae"]
        
        extractor = MetadataExtractor()
        
        # メタデータを抽出
        for file_info in file_info_list:
            try:
                extractor.extract_metadata(file_info)
            except Exception as e:
                logger.error(f"Failed to extract metadata: {str(e)}")
    
    @staticmethod
    def find_associated_files(
        file_info_list: List[FileInfo],
        associated_file_extensions: List[str]
    ) -> Dict[str, List[str]]:
        """
        関連ファイルを特定してリンク
        
        Args:
            file_info_list: ファイル情報のリスト
            associated_file_extensions: 関連ファイルとみなす拡張子のリスト
            
        Returns:
            メインファイルパスをキー、関連ファイルパスのリストを値とする辞書
        """
        # ファイル間の関連付けを管理する辞書
        associations = {}
        
        # ファイル情報をパスをキーにした辞書に変換
        file_info_dict = {info.original_path: info for info in file_info_list}
        
        # ベース名（拡張子なし）ごとにグループ化
        base_name_groups = {}
        for file_info in file_info_list:
            base_name = os.path.splitext(file_info.original_filename)[0]
            base_dir = os.path.dirname(file_info.original_path)
            key = (base_dir, base_name)
            
            if key not in base_name_groups:
                base_name_groups[key] = []
            base_name_groups[key].append(file_info)
        
        # 関連ファイルの特定
        for (base_dir, base_name), group in base_name_groups.items():
            # メインファイルとサブファイルを識別
            main_files = []
            sub_files = []
            
            for file_info in group:
                if file_info.original_extension.lower() in [ext.lower() for ext in associated_file_extensions]:
                    sub_files.append(file_info)
                else:
                    main_files.append(file_info)
            
            # サブファイルのみの場合は最初のファイルをメインファイルとする
            if not main_files and sub_files:
                main_files = [sub_files.pop(0)]
            
            # メインファイルに関連ファイルを関連付け
            for main_file in main_files:
                for sub_file in sub_files:
                    main_file.add_associated_file(sub_file)
                
                associations[main_file.original_path] = [
                    sub.original_path for sub in main_file.associated_files
                ]
        
        return associations
    
    @staticmethod
    def generate_target_paths(
        file_info_list: List[FileInfo],
        folder_elements: List[PathElement],
        filename_elements: List[PathElement],
        destination_root: str
    ) -> None:
        """
        ファイルのコピー先パスを生成
        
        Args:
            file_info_list: ファイル情報のリスト
            folder_elements: フォルダ構造のパス要素リスト
            filename_elements: ファイル名パターンのパス要素リスト
            destination_root: コピー先のルートディレクトリ
        """
        for file_info in file_info_list:
            try:
                target_path = PathGenerator.generate_target_path(
                    file_info, folder_elements, filename_elements, destination_root
                )
                file_info.set_target_path(target_path)
                
                # 関連ファイルのパスも生成
                for assoc_file in file_info.associated_files:
                    assoc_target_path = PathGenerator.generate_target_path(
                        assoc_file, folder_elements, filename_elements, destination_root
                    )
                    assoc_file.set_target_path(assoc_target_path)
            
            except Exception as e:
                logger.error(f"Failed to generate target path: {str(e)}")
                file_info.set_status("error", f"Failed to generate target path: {str(e)}")
    
    @staticmethod
    def check_duplicates(
        file_info_list: List[FileInfo],
        hash_algorithm: str = "sha256"
    ) -> Dict[str, List[FileInfo]]:
        """
        重複ファイルを確認
        
        Args:
            file_info_list: ファイル情報のリスト
            hash_algorithm: ハッシュアルゴリズム
            
        Returns:
            同じハッシュ値を持つファイルのリストを値とする辞書
        """
        # ハッシュ値をキーにしたファイル情報のリストの辞書
        hash_groups = {}
        
        for file_info in file_info_list:
            try:
                # ターゲットパスが設定されていない場合はスキップ
                if not file_info.target_path:
                    continue
                
                # ハッシュ値を計算
                file_hash = file_info.calculate_hash(hash_algorithm)
                
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                
                hash_groups[file_hash].append(file_info)
            except Exception as e:
                logger.error(f"Failed to calculate hash: {str(e)}")
        
        # 重複しているグループのみを返す
        return {h: files for h, files in hash_groups.items() if len(files) > 1}
    
    @staticmethod
    def resolve_path_conflicts(
        file_info_list: List[FileInfo],
        duplicate_handling: Literal["skip", "overwrite", "rename", "ask"] = "rename"
    ) -> None:
        """
        コピー先のパス衝突を解決
        
        Args:
            file_info_list: ファイル情報のリスト
            duplicate_handling: 重複時の処理方法
        """
        # パスをキーにしたファイル情報のリストの辞書
        path_groups = {}
        
        # パスごとのグループを作成
        for file_info in file_info_list:
            if not file_info.target_path:
                continue
                
            if file_info.target_path not in path_groups:
                path_groups[file_info.target_path] = []
            
            path_groups[file_info.target_path].append(file_info)
            
            # 関連ファイルも処理
            for assoc_file in file_info.associated_files:
                if not assoc_file.target_path:
                    continue
                    
                if assoc_file.target_path not in path_groups:
                    path_groups[assoc_file.target_path] = []
                
                path_groups[assoc_file.target_path].append(assoc_file)
        
        # 衝突するパスについて処理
        for target_path, info_list in path_groups.items():
            if len(info_list) <= 1:
                continue
            
            if duplicate_handling == "skip":
                # 最初のファイル以外をスキップ
                for file_info in info_list[1:]:
                    file_info.set_status("skipped", "Duplicate path")
            
            elif duplicate_handling == "overwrite":
                # 最新のファイルを残して他をスキップ
                sorted_list = sorted(
                    info_list,
                    key=lambda x: x.last_modified,
                    reverse=True
                )
                # 最新以外はスキップ
                for file_info in sorted_list[1:]:
                    file_info.set_status("skipped", "Older duplicate")
            
            elif duplicate_handling == "rename":
                # 2番目以降のファイルの名前を変更
                for i, file_info in enumerate(info_list[1:], 1):
                    base_path, ext = os.path.splitext(target_path)
                    new_path = f"{base_path}_{i}{ext}"
                    file_info.set_target_path(new_path)
            
            # "ask"の場合はUIが処理するので、ここでは何もしない
    
    @staticmethod
    def copy_files(
        file_info_list: List[FileInfo],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> int:
        """
        ファイルをコピー
        
        Args:
            file_info_list: ファイル情報のリスト
            progress_callback: 進捗を通知するコールバック関数
            
        Returns:
            コピーに成功したファイルの数
        """
        # コピー対象ファイルの情報
        total_files = sum(
            1 for f in file_info_list
            if f.status == "pending" and f.target_path is not None
        )
        processed_files = 0
        success_count = 0
        
        # ファイルをコピー
        for file_info in file_info_list:
            # ペンディング状態でパスが設定されている場合のみ処理
            if file_info.status != "pending" or not file_info.target_path:
                continue
            
            try:
                # コピー先ディレクトリを作成
                target_dir = os.path.dirname(file_info.target_path)
                os.makedirs(target_dir, exist_ok=True)
                
                # ファイルをコピー
                shutil.copy2(file_info.original_path, file_info.target_path)
                file_info.set_status("copied")
                success_count += 1
                
                # 関連ファイルもコピー
                for assoc_file in file_info.associated_files:
                    if assoc_file.status != "pending" or not assoc_file.target_path:
                        continue
                    
                    try:
                        # 関連ファイルのコピー先ディレクトリを作成
                        assoc_target_dir = os.path.dirname(assoc_file.target_path)
                        os.makedirs(assoc_target_dir, exist_ok=True)
                        
                        # 関連ファイルをコピー
                        shutil.copy2(assoc_file.original_path, assoc_file.target_path)
                        assoc_file.set_status("copied")
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to copy associated file: {str(e)}")
                        assoc_file.set_status("error", str(e))
            
            except Exception as e:
                logger.error(f"Failed to copy file: {str(e)}")
                file_info.set_status("error", str(e))
            
            # 進捗を通知
            processed_files += 1
            if progress_callback:
                progress_callback(
                    processed_files, total_files, file_info.original_filename
                )
        
        return success_count 