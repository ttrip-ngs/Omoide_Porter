#!/usr/bin/env python
"""
動画・写真コピーユーティリティ - メインウィンドウ
モダンな統合型ファイル管理アプリケーションのUI
"""

import os
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core.config_manager import ConfigManager
from ..core.device_manager import DeviceManager
from ..core.file_operations import FileOperations
from ..core.models import ConnectionStatus, DeviceInfo, DeviceType, SourceType


class ModernFileManagerWindow(QMainWindow):
    """モダンな統合型ファイル管理メインウィンドウ"""

    def __init__(self):
        super().__init__()

        # コアコンポーネントの初期化
        self.config_manager = ConfigManager()
        self.device_manager = DeviceManager()
        self.file_operations = FileOperations()

        # UI状態管理
        self.current_source_path = ""
        self.current_destination_path = ""
        self.selected_files = []
        self.preview_files = []
        self.connected_devices = []

        # ワーカースレッド
        self.worker_thread = None

        self._setup_ui()
        self._setup_connections()
        self._apply_modern_styling()
        self._start_device_monitoring()

        # プリセットを読み込み
        self._load_presets()

    def _setup_ui(self):
        """モダンなUIレイアウトを設定"""
        # ウィンドウの基本設定
        self.setWindowTitle("動画・写真コピーユーティリティ")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        # セントラルウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト（水平分割）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # サイドバー（左側）
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # メインコンテンツエリア（右側）
        main_content = self._create_main_content()
        main_layout.addWidget(main_content)

        # ツールバーの作成
        self._create_toolbar()

        # ステータスバーの作成
        self._create_status_bar()

        # メニューバーの作成
        self._create_menu_bar()

    def _create_sidebar(self) -> QWidget:
        """サイドバーを作成（デバイス・プリセット・お気に入り）"""
        sidebar = QFrame()
        sidebar.setFixedWidth(280)
        sidebar.setFrameStyle(QFrame.Shape.StyledPanel)
        sidebar.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d30;
                border-right: 1px solid #3e3e42;
            }
        """
        )

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ソース選択セクション
        source_section = self._create_source_section()
        layout.addWidget(source_section)

        # デバイスセクション
        devices_section = self._create_devices_section()
        layout.addWidget(devices_section)

        # プリセットセクション
        presets_section = self._create_presets_section()
        layout.addWidget(presets_section)

        layout.addStretch()

        return sidebar

    def _create_source_section(self) -> QWidget:
        """ソース選択セクションを作成"""
        section = QGroupBox("ソース")
        section.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(section)
        layout.setSpacing(8)

        # フォルダ選択
        folder_btn = QPushButton("📁 フォルダを選択")
        folder_btn.clicked.connect(self._browse_source_folder)
        layout.addWidget(folder_btn)

        # 選択されたパス表示
        self.source_path_label = QLabel("未選択")
        self.source_path_label.setWordWrap(True)
        self.source_path_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        layout.addWidget(self.source_path_label)

        return section

    def _create_devices_section(self) -> QWidget:
        """デバイスセクションを作成"""
        section = QGroupBox("接続デバイス")
        section.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(section)
        layout.setSpacing(8)

        # デバイス検出ボタン
        detect_btn = QPushButton("🔍 デバイス検出")
        detect_btn.clicked.connect(self._detect_devices)
        layout.addWidget(detect_btn)

        # デバイスリスト
        self.device_list = QListWidget()
        self.device_list.setMaximumHeight(120)
        self.device_list.setStyleSheet(
            """
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
            }
        """
        )
        layout.addWidget(self.device_list)

        return section

    def _create_presets_section(self) -> QWidget:
        """プリセットセクションを作成"""
        section = QGroupBox("プリセット")
        section.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(section)
        layout.setSpacing(8)

        # プリセット選択
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(
            ["デフォルト", "旅行写真", "イベント動画", "RAW写真"]
        )
        layout.addWidget(self.preset_combo)

        # プリセット管理ボタン
        preset_buttons = QHBoxLayout()

        new_preset_btn = QPushButton("新規")
        new_preset_btn.clicked.connect(self._create_new_preset)
        preset_buttons.addWidget(new_preset_btn)

        edit_preset_btn = QPushButton("編集")
        edit_preset_btn.clicked.connect(self._edit_preset)
        preset_buttons.addWidget(edit_preset_btn)

        layout.addLayout(preset_buttons)

        return section

    def _create_main_content(self) -> QWidget:
        """メインコンテンツエリアを作成"""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 上部：ナビゲーション＆コントロール
        nav_area = self._create_navigation_area()
        layout.addWidget(nav_area)

        # 中央：メインコンテンツ（タブベース）
        self.main_tabs = QTabWidget()
        self.main_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.main_tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #3e3e42;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0e639c;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
            }
        """
        )

        # ファイルブラウザタブ
        file_browser_tab = self._create_file_browser_tab()
        self.main_tabs.addTab(file_browser_tab, "📁 ファイルブラウザ")

        # 設定タブ
        settings_tab = self._create_settings_tab()
        self.main_tabs.addTab(settings_tab, "⚙️ 設定")

        # プレビュータブ
        preview_tab = self._create_preview_tab()
        self.main_tabs.addTab(preview_tab, "👁️ プレビュー")

        # ログタブ
        log_tab = self._create_log_tab()
        self.main_tabs.addTab(log_tab, "📋 ログ")

        layout.addWidget(self.main_tabs)

        # 下部：進捗バー＆アクションボタン
        bottom_area = self._create_bottom_area()
        layout.addWidget(bottom_area)

        return content_widget

    def _create_navigation_area(self) -> QWidget:
        """ナビゲーション＆コントロールエリアを作成"""
        nav_widget = QFrame()
        nav_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        nav_widget.setStyleSheet(
            """
            QFrame {
                background-color: #3c3c3c;
                border-bottom: 1px solid #3e3e42;
            }
        """
        )
        nav_widget.setFixedHeight(60)

        layout = QHBoxLayout(nav_widget)
        layout.setContentsMargins(16, 8, 16, 8)

        # パンくずリスト
        breadcrumb_label = QLabel("ホーム > ドキュメント > 写真")
        breadcrumb_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        layout.addWidget(breadcrumb_label)

        layout.addStretch()

        # 表示切り替えボタン
        view_group = QButtonGroup()

        list_view_btn = QPushButton("📋")
        list_view_btn.setCheckable(True)
        list_view_btn.setChecked(True)
        list_view_btn.setToolTip("リスト表示")
        view_group.addButton(list_view_btn)
        layout.addWidget(list_view_btn)

        grid_view_btn = QPushButton("⊞")
        grid_view_btn.setCheckable(True)
        grid_view_btn.setToolTip("グリッド表示")
        view_group.addButton(grid_view_btn)
        layout.addWidget(grid_view_btn)

        # 検索フィールド
        search_field = QLineEdit()
        search_field.setPlaceholderText("ファイルを検索...")
        search_field.setFixedWidth(200)
        search_field.setStyleSheet(
            """
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """
        )
        layout.addWidget(search_field)

        return nav_widget

    def _create_file_browser_tab(self) -> QWidget:
        """ファイルブラウザタブを作成"""
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 左側：ファイルリスト
        file_area = self._create_file_list_area()
        layout.addWidget(file_area, 2)

        # 右側：プレビュー＆詳細
        preview_area = self._create_file_preview_area()
        layout.addWidget(preview_area, 1)

        return tab_widget

    def _create_file_list_area(self) -> QWidget:
        """ファイルリストエリアを作成"""
        area_widget = QFrame()
        area_widget.setFrameStyle(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(area_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # ファイルテーブル
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(6)
        self.file_table.setHorizontalHeaderLabels(
            ["名前", "サイズ", "タイプ", "更新日時", "カメラ", "状態"]
        )

        # テーブルの設定
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3e3e42;
                selection-background-color: #0e639c;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #3e3e42;
            }
        """
        )

        layout.addWidget(self.file_table)

        return area_widget

    def _create_file_preview_area(self) -> QWidget:
        """ファイルプレビューエリアを作成"""
        preview_widget = QFrame()
        preview_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        preview_widget.setStyleSheet(
            """
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
            }
        """
        )

        layout = QVBoxLayout(preview_widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # プレビューラベル
        preview_title = QLabel("ファイルプレビュー")
        preview_title.setStyleSheet(
            "color: #ffffff; font-weight: bold; font-size: 14px;"
        )
        layout.addWidget(preview_title)

        # プレビュー画像エリア
        self.preview_label = QLabel()
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            """
            QLabel {
                border: 1px solid #3e3e42;
                background-color: #1e1e1e;
                color: #cccccc;
            }
        """
        )
        self.preview_label.setText("ファイルを選択してください")
        layout.addWidget(self.preview_label)

        # メタデータ表示
        metadata_title = QLabel("メタデータ")
        metadata_title.setStyleSheet(
            "color: #ffffff; font-weight: bold; font-size: 12px; margin-top: 16px;"
        )
        layout.addWidget(metadata_title)

        self.metadata_text = QTextEdit()
        self.metadata_text.setMaximumHeight(150)
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """
        )
        layout.addWidget(self.metadata_text)

        layout.addStretch()

        return preview_widget

    def _create_settings_tab(self) -> QWidget:
        """設定タブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        # スクロールエリア
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # コピー先設定
        dest_group = self._create_destination_settings()
        scroll_layout.addWidget(dest_group)

        # フォルダ構造設定
        folder_group = self._create_folder_structure_settings()
        scroll_layout.addWidget(folder_group)

        # ファイル名設定
        filename_group = self._create_filename_settings()
        scroll_layout.addWidget(filename_group)

        # 重複処理設定
        duplicate_group = self._create_duplicate_settings()
        scroll_layout.addWidget(duplicate_group)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return tab_widget

    def _create_destination_settings(self) -> QGroupBox:
        """コピー先設定グループを作成"""
        group = QGroupBox("コピー先設定")
        group.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        # コピー先選択
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("コピー先:"))

        self.dest_path_edit = QLineEdit()
        self.dest_path_edit.setPlaceholderText("コピー先フォルダを選択してください")
        dest_layout.addWidget(self.dest_path_edit)

        dest_browse_btn = QPushButton("参照...")
        dest_browse_btn.clicked.connect(self._browse_destination_folder)
        dest_layout.addWidget(dest_browse_btn)

        layout.addLayout(dest_layout)

        return group

    def _create_folder_structure_settings(self) -> QGroupBox:
        """フォルダ構造設定グループを作成"""
        group = QGroupBox("フォルダ構造設定")
        group.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        # プリセット選択
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("プリセット:"))

        folder_preset_combo = QComboBox()
        folder_preset_combo.addItems(
            [
                "{撮影年}/{撮影月}/{撮影日}",
                "{カメラモデル}/{撮影年}-{撮影月}",
                "{撮影年}/{GPS国}/{GPS都道府県}",
                "カスタム...",
            ]
        )
        preset_layout.addWidget(folder_preset_combo)

        layout.addLayout(preset_layout)

        # カスタムパターン入力
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("カスタムパターン:"))

        custom_pattern_edit = QLineEdit()
        custom_pattern_edit.setPlaceholderText("例: {撮影年}/{撮影月}/{撮影日}")
        custom_layout.addWidget(custom_pattern_edit)

        layout.addLayout(custom_layout)

        # プレビュー
        preview_label = QLabel("プレビュー: 写真/2023/10/27")
        preview_label.setStyleSheet("color: #0e639c; font-style: italic;")
        layout.addWidget(preview_label)

        return group

    def _create_filename_settings(self) -> QGroupBox:
        """ファイル名設定グループを作成"""
        group = QGroupBox("ファイル名設定")
        group.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(group)
        layout.setSpacing(12)

        # ファイル名変更オプション
        rename_check = QCheckBox("ファイル名を変更する")
        layout.addWidget(rename_check)

        # パターン選択
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("命名規則:"))

        filename_pattern_combo = QComboBox()
        filename_pattern_combo.addItems(
            [
                "{撮影年月日}_{時分秒}_{連番3桁}",
                "{カメラモデル}_{撮影年月日}_{元のファイル名}",
                "{元のファイル名}",
                "カスタム...",
            ]
        )
        pattern_layout.addWidget(filename_pattern_combo)

        layout.addLayout(pattern_layout)

        return group

    def _create_duplicate_settings(self) -> QGroupBox:
        """重複処理設定グループを作成"""
        group = QGroupBox("重複ファイル処理")
        group.setStyleSheet(self._get_groupbox_style())

        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # ラジオボタンで処理方法を選択
        skip_radio = QRadioButton("重複ファイルをスキップ")
        skip_radio.setChecked(True)
        layout.addWidget(skip_radio)

        overwrite_radio = QRadioButton("重複ファイルを上書き")
        layout.addWidget(overwrite_radio)

        rename_radio = QRadioButton("名前を変更して保存")
        layout.addWidget(rename_radio)

        confirm_radio = QRadioButton("毎回確認する")
        layout.addWidget(confirm_radio)

        return group

    def _create_preview_tab(self) -> QWidget:
        """プレビュータブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(16, 16, 16, 16)

        # プレビューコントロール
        control_layout = QHBoxLayout()

        scan_btn = QPushButton("🔍 ファイルをスキャン")
        scan_btn.clicked.connect(self._scan_files)
        control_layout.addWidget(scan_btn)

        control_layout.addStretch()

        refresh_btn = QPushButton("🔄 更新")
        control_layout.addWidget(refresh_btn)

        layout.addLayout(control_layout)

        # プレビューテーブル
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(
            ["ソースパス", "コピー先パス", "サイズ", "操作", "状態"]
        )

        # テーブルスタイリング
        self.preview_table.setStyleSheet(self.file_table.styleSheet())
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.preview_table)

        return tab_widget

    def _create_log_tab(self) -> QWidget:
        """ログタブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(16, 16, 16, 16)

        # ログコントロール
        control_layout = QHBoxLayout()

        clear_btn = QPushButton("🗑️ ログをクリア")
        clear_btn.clicked.connect(self._clear_log)
        control_layout.addWidget(clear_btn)

        control_layout.addStretch()

        log_level_combo = QComboBox()
        log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        log_level_combo.setCurrentText("Info")
        control_layout.addWidget(QLabel("ログレベル:"))
        control_layout.addWidget(log_level_combo)

        layout.addLayout(control_layout)

        # ログ表示エリア
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """
        )
        layout.addWidget(self.log_text)

        return tab_widget

    def _create_bottom_area(self) -> QWidget:
        """下部エリア（進捗バー＆アクションボタン）を作成"""
        bottom_widget = QFrame()
        bottom_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        bottom_widget.setStyleSheet(
            """
            QFrame {
                background-color: #3c3c3c;
                border-top: 1px solid #3e3e42;
            }
        """
        )
        bottom_widget.setFixedHeight(80)

        layout = QHBoxLayout(bottom_widget)
        layout.setContentsMargins(16, 12, 16, 12)

        # 進捗バー
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("準備完了")
        self.progress_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #3e3e42;
                border-radius: 4px;
                text-align: center;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 3px;
            }
        """
        )
        progress_layout.addWidget(self.progress_bar)

        layout.addLayout(progress_layout)

        layout.addStretch()

        # アクションボタン
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.preview_btn = QPushButton("👁️ プレビュー")
        self.preview_btn.setFixedSize(120, 36)
        self.preview_btn.clicked.connect(self._preview_operation)
        button_layout.addWidget(self.preview_btn)

        self.copy_btn = QPushButton("📋 コピー開始")
        self.copy_btn.setFixedSize(120, 36)
        self.copy_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0a4d7a;
            }
        """
        )
        self.copy_btn.clicked.connect(self._start_copy_operation)
        button_layout.addWidget(self.copy_btn)

        layout.addLayout(button_layout)

        return bottom_widget

    def _create_toolbar(self):
        """ツールバーを作成"""
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet(
            """
            QToolBar {
                background-color: #2d2d30;
                border: none;
                spacing: 8px;
            }
            QToolButton {
                color: #ffffff;
                padding: 8px;
                border: none;
            }
            QToolButton:hover {
                background-color: #3e3e42;
                border-radius: 4px;
            }
        """
        )

        # ツールバーアクション
        new_action = QAction("📁", self)
        new_action.setText("新規")
        new_action.setToolTip("新しいプロジェクトを作成")
        toolbar.addAction(new_action)

        open_action = QAction("📂", self)
        open_action.setText("開く")
        open_action.setToolTip("プロジェクトを開く")
        toolbar.addAction(open_action)

        save_action = QAction("💾", self)
        save_action.setText("保存")
        save_action.setToolTip("プロジェクトを保存")
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        settings_action = QAction("⚙️", self)
        settings_action.setText("設定")
        settings_action.setToolTip("設定を開く")
        toolbar.addAction(settings_action)

        help_action = QAction("❓", self)
        help_action.setText("ヘルプ")
        help_action.setToolTip("ヘルプを表示")
        toolbar.addAction(help_action)

        self.addToolBar(toolbar)

    def _create_menu_bar(self):
        """メニューバーを作成"""
        menubar = self.menuBar()
        menubar.setStyleSheet(
            """
            QMenuBar {
                background-color: #2d2d30;
                color: #ffffff;
                border-bottom: 1px solid #3e3e42;
            }
            QMenuBar::item {
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #3e3e42;
            }
        """
        )

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")
        file_menu.addAction("新規プロジェクト")
        file_menu.addAction("プロジェクトを開く")
        file_menu.addAction("プロジェクトを保存")
        file_menu.addSeparator()
        file_menu.addAction("終了")

        # 編集メニュー
        edit_menu = menubar.addMenu("編集(&E)")
        edit_menu.addAction("設定")
        edit_menu.addAction("プリセット管理")

        # 表示メニュー
        view_menu = menubar.addMenu("表示(&V)")
        view_menu.addAction("リスト表示")
        view_menu.addAction("グリッド表示")
        view_menu.addAction("プレビューパネル")

        # ツールメニュー
        tools_menu = menubar.addMenu("ツール(&T)")
        tools_menu.addAction("ファイルスキャン")
        tools_menu.addAction("重複ファイル検索")
        tools_menu.addAction("メタデータ抽出")

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")
        help_menu.addAction("ユーザーガイド")
        help_menu.addAction("バージョン情報")

    def _create_status_bar(self):
        """ステータスバーを作成"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet(
            """
            QStatusBar {
                background-color: #2d2d30;
                color: #ffffff;
                border-top: 1px solid #3e3e42;
            }
        """
        )

        # 左側：一般的なステータス
        status_bar.showMessage("準備完了")

        # 右側：追加情報
        self.status_files_label = QLabel("ファイル数: 0")
        self.status_files_label.setStyleSheet("margin-right: 8px;")
        status_bar.addPermanentWidget(self.status_files_label)

        self.status_size_label = QLabel("合計サイズ: 0 B")
        status_bar.addPermanentWidget(self.status_size_label)

        self.setStatusBar(status_bar)

    def _get_groupbox_style(self) -> str:
        """GroupBox共通スタイルを取得"""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """

    def _apply_modern_styling(self):
        """モダンなスタイリングを適用"""
        # ダークテーマの適用
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #0e639c;
            }
            QLabel {
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QRadioButton {
                color: #ffffff;
            }
        """
        )

    def _setup_connections(self):
        """シグナル・スロット接続を設定"""
        # ファイルテーブルの選択変更
        self.file_table.itemSelectionChanged.connect(self._file_selection_changed)

        # プリセット選択変更
        self.preset_combo.currentTextChanged.connect(self._preset_changed)

        # デバイスリストの選択変更
        self.device_list.itemClicked.connect(self._device_selected)

    def _start_device_monitoring(self):
        """デバイス監視を開始"""
        # デバイス監視タイマー
        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self._detect_devices)
        self.device_timer.start(5000)  # 5秒間隔

    # イベントハンドラメソッド
    def _browse_source_folder(self):
        """ソースフォルダを参照"""
        folder = QFileDialog.getExistingDirectory(self, "ソースフォルダを選択")
        if folder:
            self.current_source_path = folder
            self.source_path_label.setText(folder)
            self._log_message(f"ソースフォルダを選択: {folder}")

    def _browse_destination_folder(self):
        """コピー先フォルダを参照"""
        folder = QFileDialog.getExistingDirectory(self, "コピー先フォルダを選択")
        if folder:
            self.current_destination_path = folder
            self.dest_path_edit.setText(folder)
            self._log_message(f"コピー先フォルダを選択: {folder}")

    def _detect_devices(self):
        """デバイス検出"""
        try:
            devices = self.device_manager.get_connected_devices()
            self.connected_devices = devices
            self._update_device_list()
        except Exception as e:
            self._log_message(f"デバイス検出エラー: {str(e)}")

    def _update_device_list(self):
        """デバイスリストを更新"""
        self.device_list.clear()
        for device in self.connected_devices:
            item_text = f"{device.display_name} ({device.device_type.value})"
            if device.connection_status == ConnectionStatus.AVAILABLE:
                item_text += " ✅"
            elif device.connection_status == ConnectionStatus.AUTHORIZATION_REQUIRED:
                item_text += " 🔐"
            else:
                item_text += " ❌"

            item = QListWidgetItem(item_text)
            self.device_list.addItem(item)

    def _update_file_list(self):
        """ファイルリストを更新"""
        self.file_table.setRowCount(0)

        if not self.selected_files:
            return

        self.file_table.setRowCount(len(self.selected_files))

        for row, file_info in enumerate(self.selected_files):
            # ファイル名
            filename_item = QTableWidgetItem(file_info.original_filename)
            self.file_table.setItem(row, 0, filename_item)

            # ファイルサイズ
            size_item = QTableWidgetItem(file_info.size_human_readable)
            self.file_table.setItem(row, 1, size_item)

            # ファイルタイプ
            type_item = QTableWidgetItem(file_info.media_type)
            self.file_table.setItem(row, 2, type_item)

            # 更新日時
            modified_text = ""
            if file_info.last_modified:
                modified_text = file_info.last_modified.strftime("%Y/%m/%d %H:%M")
            modified_item = QTableWidgetItem(modified_text)
            self.file_table.setItem(row, 3, modified_item)

    def _scan_files(self):
        """ファイルをスキャン"""
        if not self.current_source_path:
            QMessageBox.warning(self, "警告", "ソースフォルダを選択してください")
            return

        self._log_message("ファイルスキャンを開始...")

        try:
            # プログレスバーを表示
            self.progress_bar.setVisible(True)
            self.progress_label.setText("ファイルをスキャン中...")

            # ファイルをスキャン
            from ..core.file_filter import FileFilter

            file_filter = FileFilter()  # デフォルトフィルタ

            self.selected_files = self.file_operations.scan_directory(
                self.current_source_path, recursive=True, file_filter=file_filter
            )

            # ファイルリストを更新
            self._update_file_list()

            # プログレスバーを非表示
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")

            self._log_message(
                f"スキャン完了: {len(self.selected_files)}件のファイルが見つかりました"
            )

        except Exception as e:
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")
            error_msg = f"ファイルスキャンエラー: {str(e)}"
            self._log_message(error_msg)
            QMessageBox.critical(self, "エラー", error_msg)

    def _preview_operation(self):
        """操作のプレビュー"""
        if not self.current_source_path or not self.current_destination_path:
            QMessageBox.warning(
                self, "警告", "ソースとコピー先の両方を選択してください"
            )
            return

        if not self.selected_files:
            QMessageBox.warning(self, "警告", "ファイルをスキャンしてください")
            return

        self._log_message("プレビューを生成中...")

        try:
            # プリセット設定を取得（現在は簡単な例）
            folder_pattern = "写真/{撮影年}/{撮影月}"
            filename_pattern = "{元のファイル名}"

            # パスを生成
            from ..core.path_generator import (
                LiteralElement,
                MetadataElement,
                OriginalFilenameElement,
                PathGenerator,
            )

            folder_elements = [
                LiteralElement("写真"),
                MetadataElement("year"),
                MetadataElement("month"),
            ]

            filename_elements = [OriginalFilenameElement()]

            # ターゲットパスを生成
            self.file_operations.generate_target_paths(
                self.selected_files,
                folder_elements,
                filename_elements,
                self.current_destination_path,
            )

            # プレビューファイルを更新
            self.preview_files = self.selected_files.copy()

            # プレビューリストを更新
            self._update_preview_list()

            self._log_message(f"プレビュー生成完了: {len(self.preview_files)}件")

        except Exception as e:
            error_msg = f"プレビュー生成エラー: {str(e)}"
            self._log_message(error_msg)
            QMessageBox.critical(self, "エラー", error_msg)

    def _update_preview_list(self):
        """プレビューリストを更新"""
        # プレビュータブ内のテキストエリアに結果を表示
        preview_text = "コピープレビュー:\n\n"

        for file_info in self.preview_files[:20]:  # 最初の20件のみ表示
            source_path = file_info.original_path
            target_path = file_info.target_path
            preview_text += f"● {source_path}\n   → {target_path}\n\n"

        if len(self.preview_files) > 20:
            preview_text += f"... 他 {len(self.preview_files) - 20} 件"

        # プレビューラベルを更新
        self.preview_label.setText(preview_text)

    def _start_copy_operation(self):
        """コピー操作を開始"""
        if not self.current_source_path or not self.current_destination_path:
            QMessageBox.warning(
                self, "警告", "ソースとコピー先の両方を選択してください"
            )
            return

        if not self.selected_files:
            QMessageBox.warning(self, "警告", "ファイルをスキャンしてください")
            return

        reply = QMessageBox.question(
            self,
            "確認",
            f"{len(self.selected_files)}件のファイルをコピーしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._log_message("コピー操作を開始...")
            self.progress_bar.setVisible(True)
            self.progress_label.setText("コピー中...")

            try:
                # プログレスコールバック
                def progress_callback(current, total, filename):
                    progress_percent = (current / total) * 100
                    self.progress_bar.setValue(int(progress_percent))
                    self.progress_label.setText(
                        f"コピー中: {filename} ({current}/{total})"
                    )
                    QApplication.processEvents()  # UIを更新

                # コピーを実行
                copied_count = self.file_operations.copy_files(
                    self.selected_files, progress_callback=progress_callback
                )

                # 完了
                self.progress_bar.setVisible(False)
                self.progress_label.setText("")

                self._log_message(
                    f"コピー完了: {copied_count}件のファイルをコピーしました"
                )
                QMessageBox.information(
                    self, "完了", f"{copied_count}件のファイルのコピーが完了しました。"
                )

                # ファイルリストを更新
                self._update_file_list()

            except Exception as e:
                self.progress_bar.setVisible(False)
                self.progress_label.setText("")
                error_msg = f"コピーエラー: {str(e)}"
                self._log_message(error_msg)
                QMessageBox.critical(self, "エラー", error_msg)

    def _file_selection_changed(self):
        """ファイル選択変更時の処理"""
        selected_items = self.file_table.selectedItems()
        if selected_items:
            # プレビュー更新
            self.preview_label.setText(
                "選択されたファイル:\n" + str(len(selected_items)) + "件"
            )
            # TODO: 実際のプレビュー表示処理

    def _preset_changed(self, preset_name: str):
        """プリセット変更時の処理"""
        self._log_message(f"プリセットを変更: {preset_name}")
        try:
            # プリセットを読み込み
            preset_config = self.config_manager.load_preset(preset_name)
            if preset_config:
                # コピー先設定を適用
                if preset_config.get("destination_path"):
                    self.current_destination_path = preset_config["destination_path"]
                    self.dest_path_edit.setText(self.current_destination_path)

                self._log_message(f"プリセット '{preset_name}' を適用しました")
            else:
                self._log_message(f"プリセット '{preset_name}' が見つかりません")
        except Exception as e:
            self._log_message(f"プリセット読み込みエラー: {str(e)}")

    def _create_new_preset(self):
        """新規プリセットを作成"""
        from .preset_dialog import PresetManagementDialog

        dialog = PresetManagementDialog(self)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            # プリセットコンボボックスを更新
            self._load_presets()
            self._log_message("新規プリセットが作成されました")

    def _edit_preset(self):
        """プリセットを編集"""
        current_preset = self.preset_combo.currentText()
        if current_preset == "デフォルト":
            QMessageBox.information(
                self, "情報", "デフォルトプリセットは編集できません"
            )
            return

        from .preset_dialog import PresetManagementDialog

        dialog = PresetManagementDialog(self, current_preset)
        if dialog.exec() == QMessageBox.StandardButton.Ok:
            # プリセットコンボボックスを更新
            self._load_presets()
            self._log_message(f"プリセット '{current_preset}' が更新されました")

    def _load_presets(self):
        """プリセット一覧を読み込んでコンボボックスを更新"""
        try:
            presets = self.config_manager.list_presets()

            # 現在の選択を保存
            current_selection = self.preset_combo.currentText()

            # アイテムをクリア
            self.preset_combo.clear()

            # プリセットを追加
            for preset in presets:
                self.preset_combo.addItem(preset)

            # 以前の選択を復元
            index = self.preset_combo.findText(current_selection)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)

        except Exception as e:
            self._log_message(f"プリセット読み込みエラー: {str(e)}")

    def _clear_log(self):
        """ログをクリア"""
        self.log_text.clear()

    def _log_message(self, message: str):
        """ログメッセージを追加"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)

        # ログを最下部にスクロール
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _device_selected(self, item: QListWidgetItem):
        """デバイス選択時の処理"""
        text = item.text()
        self._log_message(f"デバイスを選択: {text}")
        # TODO: 実際のデバイス選択処理


def main():
    """メイン関数"""
    app = QApplication(sys.argv)

    # アプリケーション設定
    app.setApplicationName("動画・写真コピーユーティリティ")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Video Copy Tool")

    # メインウィンドウを作成して表示
    window = ModernFileManagerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
