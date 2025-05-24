import hashlib
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


class FileInfo:
    """ファイル情報を保持するクラス"""

    def __init__(self, original_path: str, source_device: Optional[str] = None):
        """
        Args:
            original_path: 元のファイルのパス
            source_device: ソースデバイスタイプ (iOS, Android, Camera等)
        """
        self.original_path = original_path
        self.original_filename = os.path.basename(original_path)
        self.original_extension = os.path.splitext(self.original_filename)[1].lower()[
            1:
        ]
        self.source_device = source_device

        # ファイルの基本情報
        stat = os.stat(original_path)
        self.size = stat.st_size
        self.last_modified = datetime.fromtimestamp(stat.st_mtime)

        # 種別の推定
        self.media_type = self._guess_media_type()

        # 後で設定される情報
        self.metadata: Dict[str, Any] = {}
        self.hash: Optional[str] = None
        self.target_path: Optional[str] = None
        self.target_filename: Optional[str] = None
        self.status: Literal["pending", "copied", "skipped", "error"] = "pending"
        self.associated_files: List["FileInfo"] = []
        self.error_message: Optional[str] = None

        # スクリーンショット判定結果のキャッシュ
        self._is_screenshot_cache: Optional[bool] = None

    def _guess_media_type(self) -> Literal["video", "image", "audio", "raw", "unknown"]:
        """ファイル拡張子からメディア種別を推定"""
        video_extensions = {"mp4", "mov", "avi", "wmv", "m4v", "mts", "m2ts"}
        image_extensions = {
            "jpg",
            "jpeg",
            "png",
            "gif",
            "tiff",
            "tif",
            "bmp",
            "heic",
            "heif",
        }
        audio_extensions = {"mp3", "wav", "aac", "flac", "m4a"}
        raw_extensions = {"arw", "raw", "cr2", "cr3", "nef", "orf", "rw2", "dng"}

        ext = self.original_extension.lower()

        if ext in video_extensions:
            return "video"
        elif ext in image_extensions:
            return "image"
        elif ext in audio_extensions:
            return "audio"
        elif ext in raw_extensions:
            return "raw"
        else:
            return "unknown"

    def is_screenshot(self) -> bool:
        """
        ファイルがスクリーンショットかどうかを判定

        Returns:
            スクリーンショットの場合True、そうでなければFalse
        """
        if self._is_screenshot_cache is not None:
            return self._is_screenshot_cache

        # 画像以外はスクリーンショットではない
        if self.media_type != "image":
            self._is_screenshot_cache = False
            return False

        # ファイル名パターンによる判定
        if self._is_screenshot_by_filename():
            self._is_screenshot_cache = True
            return True

        # ファイルパスによる判定
        if self._is_screenshot_by_path():
            self._is_screenshot_cache = True
            return True

        # メタデータによる判定（後でメタデータが設定された後に再判定される可能性あり）
        if self._is_screenshot_by_metadata():
            self._is_screenshot_cache = True
            return True

        self._is_screenshot_cache = False
        return False

    def _is_screenshot_by_filename(self) -> bool:
        """ファイル名パターンでスクリーンショットかどうかを判定"""
        filename = self.original_filename.lower()

        # iOSスクリーンショットパターン
        ios_patterns = [
            r"^img_\d{4}\.png$",  # IMG_0001.PNG
            r"^screenshot.*\.png$",  # Screenshot_*.png
            r"^スクリーンショット.*\.png$",  # 日本語設定の場合
        ]

        # Androidスクリーンショットパターン
        android_patterns = [
            r"^screenshot.*\.png$",
            r"^screenshot_\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}.*\.png$",
            r"^スクリーンショット.*\.png$",
        ]

        all_patterns = ios_patterns + android_patterns

        for pattern in all_patterns:
            if re.match(pattern, filename):
                return True

        return False

    def _is_screenshot_by_path(self) -> bool:
        """ファイルパスでスクリーンショットかどうかを判定"""
        path_lower = self.original_path.lower().replace("\\", "/")

        # スクリーンショット用フォルダのパターン
        screenshot_paths = [
            "/pictures/screenshots/",
            "/pictures/",  # Android/iOS共通
            "/dcim/screenshots/",
            "/screenshot/",
            "/スクリーンショット/",
        ]

        # DCIM以外のPicturesフォルダの場合はスクリーンショットの可能性が高い（iOS）
        if "/pictures/" in path_lower and "/dcim/" not in path_lower:
            # ただし、拡張子がPNGの場合のみ
            if self.original_extension.lower() == "png":
                return True

        for screenshot_path in screenshot_paths:
            if screenshot_path in path_lower:
                return True

        return False

    def _is_screenshot_by_metadata(self) -> bool:
        """メタデータでスクリーンショットかどうかを判定"""
        # メタデータが未設定の場合は判定できない
        if not self.metadata:
            return False

        # ImageDescriptionフィールドをチェック
        image_desc = self.metadata.get("image_description", "").lower()
        if "screenshot" in image_desc or "スクリーンショット" in image_desc:
            return True

        # Softwareフィールドをチェック
        software = self.metadata.get("software", "").lower()
        if "screenshot" in software:
            return True

        # デバイス特有の判定
        if self.source_device == "iOS":
            return self._is_ios_screenshot_by_metadata()
        elif self.source_device == "Android":
            return self._is_android_screenshot_by_metadata()

        return False

    def _is_ios_screenshot_by_metadata(self) -> bool:
        """iOS特有のメタデータでスクリーンショット判定"""
        # iOSデバイスの画面解像度パターン
        ios_screen_resolutions = [
            (1125, 2436),
            (1242, 2688),
            (828, 1792),  # iPhone X系
            (750, 1334),
            (1242, 2208),  # iPhone 6/7/8系
            (640, 1136),
            (640, 960),
            (320, 480),  # 古いiPhone
            (1668, 2388),
            (2048, 2732),
            (1536, 2048),  # iPad
        ]

        width = self.metadata.get("width", 0)
        height = self.metadata.get("height", 0)

        if width and height:
            # 縦横どちらでも一致すればスクリーンショットの可能性
            for w, h in ios_screen_resolutions:
                if (width == w and height == h) or (width == h and height == w):
                    # PNGファイルならスクリーンショットの可能性が高い
                    return self.original_extension.lower() == "png"

        return False

    def _is_android_screenshot_by_metadata(self) -> bool:
        """Android特有のメタデータでスクリーンショット判定"""
        # 一般的なAndroid画面解像度（多様すぎるため基本チェックのみ）
        # 主にファイルパスや名前で判定する
        return False

    def reset_screenshot_cache(self) -> None:
        """スクリーンショット判定キャッシュをリセット（メタデータ更新後に呼び出し）"""
        self._is_screenshot_cache = None

    @property
    def size_human_readable(self) -> str:
        """人間が読みやすい形式でファイルサイズを取得"""
        if self.size == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(self.size)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    def calculate_hash(self, algorithm: str = "sha256") -> str:
        """
        ファイルのハッシュ値を計算

        Args:
            algorithm: ハッシュアルゴリズム ("sha256", "md5", "sha1")

        Returns:
            ハッシュ値（16進数文字列）
        """
        if self.hash:
            return self.hash

        hash_func = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
        }.get(algorithm.lower(), hashlib.sha256)()

        with open(self.original_path, "rb") as f:
            # バッファリングしてファイルを読み込む
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        self.hash = hash_func.hexdigest()
        return self.hash

    def set_target_path(self, full_path: str) -> None:
        """コピー先のパスを設定"""
        self.target_path = full_path
        self.target_filename = os.path.basename(full_path)

    def set_status(
        self,
        status: Literal["pending", "copied", "skipped", "error"],
        error_message: Optional[str] = None,
    ) -> None:
        """
        処理状態を設定

        Args:
            status: 処理状態
            error_message: エラーメッセージ（エラー時のみ）
        """
        self.status = status
        if error_message:
            self.error_message = error_message

    def add_associated_file(self, file_info: "FileInfo") -> None:
        """関連ファイルを追加"""
        self.associated_files.append(file_info)

    def __str__(self) -> str:
        return f"FileInfo({self.original_filename}, {self.media_type}, {self.status})"

    def __repr__(self) -> str:
        return self.__str__()
