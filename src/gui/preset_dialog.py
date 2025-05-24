#!/usr/bin/env python
"""
プリセット管理ダイアログ
フォルダ構造、ファイル名規則、その他の設定を管理
"""

import os
import sys
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager


class PresetManagementDialog(QDialog):
    """プリセット管理ダイアログ"""

    preset_saved = Signal(str)  # プリセット保存時のシグナル

    def __init__(self, parent=None, preset_name: str = ""):
        super().__init__(parent)

        self.config_manager = ConfigManager()
        self.preset_name = preset_name
        self.is_new_preset = not preset_name

        self._setup_ui()
        self._setup_connections()
        self._load_preset_data()
        self._apply_styling()

    def _setup_ui(self):
        """UIをセットアップ"""
        self.setWindowTitle(
            "プリセット設定"
            if self.is_new_preset
            else f"プリセット編集: {self.preset_name}"
        )
        self.setModal(True)
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # プリセット名入力
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("プリセット名:"))

        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setText(self.preset_name)
        self.preset_name_edit.setPlaceholderText("プリセット名を入力してください")
        name_layout.addWidget(self.preset_name_edit)

        layout.addLayout(name_layout)

        # タブウィジェット
        self.tab_widget = QTabWidget()

        # フォルダ構造タブ
        folder_tab = self._create_folder_structure_tab()
        self.tab_widget.addTab(folder_tab, "📁 フォルダ構造")

        # ファイル名規則タブ
        filename_tab = self._create_filename_rules_tab()
        self.tab_widget.addTab(filename_tab, "📝 ファイル名規則")

        # フィルタ設定タブ
        filter_tab = self._create_filter_settings_tab()
        self.tab_widget.addTab(filter_tab, "🔍 フィルタ設定")

        # 処理オプションタブ
        options_tab = self._create_processing_options_tab()
        self.tab_widget.addTab(options_tab, "⚙️ 処理オプション")

        # プレビュータブ
        preview_tab = self._create_preview_tab()
        self.tab_widget.addTab(preview_tab, "👁️ プレビュー")

        layout.addWidget(self.tab_widget)

        # ボタンエリア
        button_layout = QHBoxLayout()

        # テンプレートボタン
        template_btn = QPushButton("📋 テンプレートから作成")
        template_btn.clicked.connect(self._load_from_template)
        button_layout.addWidget(template_btn)

        button_layout.addStretch()

        # キャンセル・保存ボタン
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_preset)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _create_folder_structure_tab(self) -> QWidget:
        """フォルダ構造タブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(16)

        # 説明
        info_label = QLabel(
            "フォルダ構造を定義します。利用可能な変数をドラッグ＆ドロップまたは選択して組み合わせてください。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info_label)

        # メインエリア（分割）
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左側：利用可能な変数
        variables_widget = self._create_variables_widget()
        splitter.addWidget(variables_widget)

        # 右側：フォルダ構造設定
        structure_widget = self._create_structure_widget()
        splitter.addWidget(structure_widget)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

        return tab_widget

    def _create_variables_widget(self) -> QWidget:
        """利用可能な変数ウィジェットを作成"""
        widget = QGroupBox("利用可能な変数")
        layout = QVBoxLayout(widget)

        # 変数リスト
        self.variables_list = QTreeWidget()
        self.variables_list.setHeaderLabel("変数")

        # 変数を分類して追加
        date_item = QTreeWidgetItem(["📅 日時"])
        date_item.addChild(QTreeWidgetItem(["{撮影年} - 例: 2023"]))
        date_item.addChild(QTreeWidgetItem(["{撮影月} - 例: 10"]))
        date_item.addChild(QTreeWidgetItem(["{撮影日} - 例: 27"]))
        date_item.addChild(QTreeWidgetItem(["{撮影年月日} - 例: 20231027"]))
        date_item.addChild(QTreeWidgetItem(["{時} - 例: 14"]))
        date_item.addChild(QTreeWidgetItem(["{分} - 例: 30"]))
        date_item.addChild(QTreeWidgetItem(["{秒} - 例: 45"]))
        self.variables_list.addTopLevelItem(date_item)

        camera_item = QTreeWidgetItem(["📷 カメラ情報"])
        camera_item.addChild(QTreeWidgetItem(["{カメラメーカー} - 例: Canon"]))
        camera_item.addChild(QTreeWidgetItem(["{カメラモデル} - 例: EOS R5"]))
        camera_item.addChild(
            QTreeWidgetItem(["{レンズ} - 例: RF24-70mm F2.8 L IS USM"])
        )
        camera_item.addChild(QTreeWidgetItem(["{焦点距離} - 例: 50mm"]))
        self.variables_list.addTopLevelItem(camera_item)

        file_item = QTreeWidgetItem(["📄 ファイル情報"])
        file_item.addChild(QTreeWidgetItem(["{ファイル種別} - 例: 動画, 写真, RAW"]))
        file_item.addChild(QTreeWidgetItem(["{元のファイル名} - 例: IMG_001"]))
        file_item.addChild(QTreeWidgetItem(["{拡張子} - 例: .jpg"]))
        self.variables_list.addTopLevelItem(file_item)

        location_item = QTreeWidgetItem(["🌍 位置情報"])
        location_item.addChild(QTreeWidgetItem(["{GPS国} - 例: Japan"]))
        location_item.addChild(QTreeWidgetItem(["{GPS都道府県} - 例: Tokyo"]))
        location_item.addChild(QTreeWidgetItem(["{GPS市町村} - 例: Shibuya"]))
        self.variables_list.addTopLevelItem(location_item)

        other_item = QTreeWidgetItem(["🔧 その他"])
        other_item.addChild(QTreeWidgetItem(["{連番} - 例: 001"]))
        other_item.addChild(QTreeWidgetItem(["{連番2桁} - 例: 01"]))
        other_item.addChild(QTreeWidgetItem(["{連番3桁} - 例: 001"]))
        other_item.addChild(QTreeWidgetItem(["{プロジェクト名} - 例: 旅行2023"]))
        self.variables_list.addTopLevelItem(other_item)

        self.variables_list.expandAll()
        layout.addWidget(self.variables_list)

        # 使用方法の説明
        usage_label = QLabel(
            "変数をダブルクリックすると右側のエディタに挿入されます。\n"
            "複数の変数を組み合わせてフォルダ構造を作成できます。"
        )
        usage_label.setWordWrap(True)
        usage_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(usage_label)

        return widget

    def _create_structure_widget(self) -> QWidget:
        """フォルダ構造設定ウィジェットを作成"""
        widget = QGroupBox("フォルダ構造")
        layout = QVBoxLayout(widget)

        # プリセットボタン
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("クイックプリセット:"))

        quick_presets = [
            ("{撮影年}/{撮影月}/{撮影日}", "日付別"),
            ("{カメラモデル}/{撮影年}-{撮影月}", "カメラ・月別"),
            ("{撮影年}/{GPS国}/{GPS都道府県}", "年・場所別"),
            ("{ファイル種別}/{撮影年}/{撮影月}", "種別・日付別"),
            ("イベント/{撮影年}/{撮影月}/{撮影日}", "イベント別"),
        ]

        for pattern, name in quick_presets:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, p=pattern: self._set_folder_pattern(p))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # フォルダパターン入力
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("フォルダパターン:"))

        self.folder_pattern_edit = QLineEdit()
        self.folder_pattern_edit.setPlaceholderText("例: {撮影年}/{撮影月}/{撮影日}")
        self.folder_pattern_edit.textChanged.connect(self._update_folder_preview)
        pattern_layout.addWidget(self.folder_pattern_edit)

        layout.addLayout(pattern_layout)

        # プレビュー
        preview_group = QGroupBox("プレビュー")
        preview_layout = QVBoxLayout(preview_group)

        self.folder_preview_text = QTextEdit()
        self.folder_preview_text.setMaximumHeight(120)
        self.folder_preview_text.setReadOnly(True)
        self.folder_preview_text.setPlainText(
            "写真/2023/10/27\n動画/2023/10/27\nRAW/2023/10/27"
        )
        preview_layout.addWidget(self.folder_preview_text)

        layout.addWidget(preview_group)

        # 詳細オプション
        options_group = QGroupBox("詳細オプション")
        options_layout = QVBoxLayout(options_group)

        self.create_subfolder_check = QCheckBox("ファイル種別でサブフォルダを作成")
        self.create_subfolder_check.setChecked(True)
        options_layout.addWidget(self.create_subfolder_check)

        self.preserve_structure_check = QCheckBox("元のフォルダ構造を一部保持")
        options_layout.addWidget(self.preserve_structure_check)

        # 未知の値の処理
        unknown_layout = QHBoxLayout()
        unknown_layout.addWidget(QLabel("メタデータが取得できない場合:"))

        self.unknown_handling_combo = QComboBox()
        self.unknown_handling_combo.addItems(
            [
                "「不明」フォルダに保存",
                "「その他」フォルダに保存",
                "日付のみで分類",
                "元のファイル名を使用",
            ]
        )
        unknown_layout.addWidget(self.unknown_handling_combo)

        options_layout.addLayout(unknown_layout)

        layout.addWidget(options_group)

        return widget

    def _create_filename_rules_tab(self) -> QWidget:
        """ファイル名規則タブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setSpacing(16)

        # ファイル名変更オプション
        rename_group = QGroupBox("ファイル名変更")
        rename_layout = QVBoxLayout(rename_group)

        self.enable_rename_check = QCheckBox("ファイル名を変更する")
        self.enable_rename_check.setChecked(False)
        self.enable_rename_check.toggled.connect(self._toggle_filename_options)
        rename_layout.addWidget(self.enable_rename_check)

        # ファイル名パターン設定（初期は無効）
        self.filename_options_widget = QWidget()
        filename_options_layout = QVBoxLayout(self.filename_options_widget)

        # クイックプリセット
        pattern_preset_layout = QHBoxLayout()
        pattern_preset_layout.addWidget(QLabel("クイックプリセット:"))

        filename_presets = [
            ("{撮影年月日}_{時分秒}_{連番3桁}", "日時＋連番"),
            ("{カメラモデル}_{撮影年月日}_{元のファイル名}", "カメラ＋日付＋元名"),
            ("{撮影年月日}_{元のファイル名}", "日付＋元名"),
            ("{プロジェクト名}_{連番3桁}", "プロジェクト＋連番"),
        ]

        for pattern, name in filename_presets:
            btn = QPushButton(name)
            btn.clicked.connect(
                lambda checked, p=pattern: self._set_filename_pattern(p)
            )
            pattern_preset_layout.addWidget(btn)

        pattern_preset_layout.addStretch()
        filename_options_layout.addLayout(pattern_preset_layout)

        # パターン入力
        filename_pattern_layout = QHBoxLayout()
        filename_pattern_layout.addWidget(QLabel("ファイル名パターン:"))

        self.filename_pattern_edit = QLineEdit()
        self.filename_pattern_edit.setPlaceholderText(
            "例: {撮影年月日}_{時分秒}_{連番3桁}"
        )
        self.filename_pattern_edit.textChanged.connect(self._update_filename_preview)
        filename_pattern_layout.addWidget(self.filename_pattern_edit)

        filename_options_layout.addLayout(filename_pattern_layout)

        # プレビュー
        filename_preview_group = QGroupBox("プレビュー")
        filename_preview_layout = QVBoxLayout(filename_preview_group)

        self.filename_preview_text = QTextEdit()
        self.filename_preview_text.setMaximumHeight(100)
        self.filename_preview_text.setReadOnly(True)
        filename_preview_layout.addWidget(self.filename_preview_text)

        filename_options_layout.addWidget(filename_preview_group)

        # 詳細オプション
        filename_detail_group = QGroupBox("詳細オプション")
        filename_detail_layout = QVBoxLayout(filename_detail_group)

        # 連番設定
        counter_layout = QHBoxLayout()
        counter_layout.addWidget(QLabel("連番開始値:"))

        self.counter_start_spin = QSpinBox()
        self.counter_start_spin.setRange(0, 9999)
        self.counter_start_spin.setValue(1)
        counter_layout.addWidget(self.counter_start_spin)

        counter_layout.addWidget(QLabel("連番リセット:"))

        self.counter_reset_combo = QComboBox()
        self.counter_reset_combo.addItems(
            ["なし", "日付変更時", "フォルダ変更時", "プロジェクト変更時"]
        )
        counter_layout.addWidget(self.counter_reset_combo)

        counter_layout.addStretch()
        filename_detail_layout.addLayout(counter_layout)

        # 重複処理
        duplicate_layout = QHBoxLayout()
        duplicate_layout.addWidget(QLabel("重複ファイル名の処理:"))

        self.duplicate_handling_combo = QComboBox()
        self.duplicate_handling_combo.addItems(
            [
                "末尾に連番追加 (例: file_001.jpg)",
                "末尾に文字追加 (例: file_copy.jpg)",
                "日時を追加 (例: file_20231027.jpg)",
                "エラーとして処理",
            ]
        )
        duplicate_layout.addWidget(self.duplicate_handling_combo)

        filename_detail_layout.addLayout(duplicate_layout)

        # 大文字小文字の処理
        case_layout = QHBoxLayout()
        case_layout.addWidget(QLabel("大文字小文字:"))

        self.case_handling_combo = QComboBox()
        self.case_handling_combo.addItems(
            ["変更しない", "すべて小文字", "すべて大文字", "最初だけ大文字"]
        )
        case_layout.addWidget(self.case_handling_combo)

        case_layout.addStretch()
        filename_detail_layout.addLayout(case_layout)

        filename_options_layout.addWidget(filename_detail_group)

        self.filename_options_widget.setEnabled(False)  # 初期は無効
        rename_layout.addWidget(self.filename_options_widget)

        layout.addWidget(rename_group)
        layout.addStretch()

        return tab_widget

    def _create_filter_settings_tab(self) -> QWidget:
        """フィルタ設定タブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # ファイル種別フィルタ
        filetype_group = QGroupBox("ファイル種別フィルタ")
        filetype_layout = QVBoxLayout(filetype_group)

        filetype_checks_layout = QHBoxLayout()

        self.include_photos_check = QCheckBox("写真ファイル")
        self.include_photos_check.setChecked(True)
        filetype_checks_layout.addWidget(self.include_photos_check)

        self.include_videos_check = QCheckBox("動画ファイル")
        self.include_videos_check.setChecked(True)
        filetype_checks_layout.addWidget(self.include_videos_check)

        self.include_raw_check = QCheckBox("RAWファイル")
        self.include_raw_check.setChecked(True)
        filetype_checks_layout.addWidget(self.include_raw_check)

        self.include_others_check = QCheckBox("その他ファイル")
        self.include_others_check.setChecked(False)
        filetype_checks_layout.addWidget(self.include_others_check)

        filetype_layout.addLayout(filetype_checks_layout)

        # カスタム拡張子
        custom_ext_layout = QHBoxLayout()
        custom_ext_layout.addWidget(QLabel("追加拡張子:"))

        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText(
            "例: .tiff, .bmp, .gif (カンマ区切り)"
        )
        custom_ext_layout.addWidget(self.custom_extensions_edit)

        filetype_layout.addLayout(custom_ext_layout)

        layout.addWidget(filetype_group)

        # サイズフィルタ
        size_group = QGroupBox("ファイルサイズフィルタ")
        size_layout = QVBoxLayout(size_group)

        self.enable_size_filter_check = QCheckBox("ファイルサイズでフィルタ")
        self.enable_size_filter_check.toggled.connect(self._toggle_size_filter)
        size_layout.addWidget(self.enable_size_filter_check)

        self.size_filter_widget = QWidget()
        size_filter_layout = QHBoxLayout(self.size_filter_widget)

        size_filter_layout.addWidget(QLabel("最小サイズ:"))
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 999999)
        self.min_size_spin.setSuffix(" MB")
        size_filter_layout.addWidget(self.min_size_spin)

        size_filter_layout.addWidget(QLabel("最大サイズ:"))
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 999999)
        self.max_size_spin.setValue(1000)
        self.max_size_spin.setSuffix(" MB")
        size_filter_layout.addWidget(self.max_size_spin)

        size_filter_layout.addStretch()

        self.size_filter_widget.setEnabled(False)
        size_layout.addWidget(self.size_filter_widget)

        layout.addWidget(size_group)

        # 日付フィルタ
        date_group = QGroupBox("日付フィルタ")
        date_layout = QVBoxLayout(date_group)

        self.enable_date_filter_check = QCheckBox("撮影日でフィルタ")
        date_layout.addWidget(self.enable_date_filter_check)

        layout.addWidget(date_group)

        layout.addStretch()

        return tab_widget

    def _create_processing_options_tab(self) -> QWidget:
        """処理オプションタブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # 重複ファイル処理
        duplicate_group = QGroupBox("重複ファイル処理")
        duplicate_layout = QVBoxLayout(duplicate_group)

        self.duplicate_button_group = QButtonGroup()

        skip_radio = QRadioButton("重複ファイルをスキップ")
        skip_radio.setChecked(True)
        self.duplicate_button_group.addButton(skip_radio, 0)
        duplicate_layout.addWidget(skip_radio)

        overwrite_radio = QRadioButton("重複ファイルを上書き")
        self.duplicate_button_group.addButton(overwrite_radio, 1)
        duplicate_layout.addWidget(overwrite_radio)

        rename_radio = QRadioButton("名前を変更して保存")
        self.duplicate_button_group.addButton(rename_radio, 2)
        duplicate_layout.addWidget(rename_radio)

        confirm_radio = QRadioButton("毎回確認する")
        self.duplicate_button_group.addButton(confirm_radio, 3)
        duplicate_layout.addWidget(confirm_radio)

        layout.addWidget(duplicate_group)

        # 関連ファイル処理
        related_group = QGroupBox("関連ファイル処理")
        related_layout = QVBoxLayout(related_group)

        self.copy_related_check = QCheckBox("関連ファイルも一緒にコピー")
        self.copy_related_check.setChecked(True)
        related_layout.addWidget(self.copy_related_check)

        # 関連ファイルの詳細設定
        related_detail_layout = QHBoxLayout()
        related_detail_layout.addWidget(QLabel("関連ファイル拡張子:"))

        self.related_extensions_edit = QLineEdit()
        self.related_extensions_edit.setText(".xmp,.thm,.aae,.gpx")
        self.related_extensions_edit.setPlaceholderText("例: .xmp,.thm,.aae,.gpx")
        related_detail_layout.addWidget(self.related_extensions_edit)

        related_layout.addLayout(related_detail_layout)

        layout.addWidget(related_group)

        # パフォーマンス設定
        performance_group = QGroupBox("パフォーマンス設定")
        performance_layout = QVBoxLayout(performance_group)

        # 並列処理数
        parallel_layout = QHBoxLayout()
        parallel_layout.addWidget(QLabel("同時処理ファイル数:"))

        self.parallel_count_spin = QSpinBox()
        self.parallel_count_spin.setRange(1, 10)
        self.parallel_count_spin.setValue(3)
        parallel_layout.addWidget(self.parallel_count_spin)

        parallel_layout.addStretch()
        performance_layout.addLayout(parallel_layout)

        # ハッシュ計算
        self.calculate_hash_check = QCheckBox(
            "ファイルハッシュを計算（重複検知の精度向上）"
        )
        self.calculate_hash_check.setChecked(True)
        performance_layout.addWidget(self.calculate_hash_check)

        # メタデータ抽出
        self.extract_metadata_check = QCheckBox("詳細メタデータを抽出")
        self.extract_metadata_check.setChecked(True)
        performance_layout.addWidget(self.extract_metadata_check)

        layout.addWidget(performance_group)

        layout.addStretch()

        return tab_widget

    def _create_preview_tab(self) -> QWidget:
        """プレビュータブを作成"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # プレビュー生成ボタン
        preview_btn = QPushButton("🔄 プレビュー更新")
        preview_btn.clicked.connect(self._update_preview)
        layout.addWidget(preview_btn)

        # プレビューテキスト
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText("プレビューを更新してください...")
        layout.addWidget(self.preview_text)

        return tab_widget

    def _setup_connections(self):
        """シグナル・スロット接続を設定"""
        # 変数リストのダブルクリック
        self.variables_list.itemDoubleClicked.connect(self._insert_variable)

        # プリセット名の変更
        self.preset_name_edit.textChanged.connect(self._validate_preset_name)

    def _toggle_filename_options(self, enabled: bool):
        """ファイル名オプションの有効/無効を切り替え"""
        self.filename_options_widget.setEnabled(enabled)
        self._update_filename_preview()

    def _toggle_size_filter(self, enabled: bool):
        """サイズフィルタの有効/無効を切り替え"""
        self.size_filter_widget.setEnabled(enabled)

    def _set_folder_pattern(self, pattern: str):
        """フォルダパターンを設定"""
        self.folder_pattern_edit.setText(pattern)
        self._update_folder_preview()

    def _set_filename_pattern(self, pattern: str):
        """ファイル名パターンを設定"""
        self.filename_pattern_edit.setText(pattern)
        self._update_filename_preview()

    def _update_folder_preview(self):
        """フォルダプレビューを更新"""
        pattern = self.folder_pattern_edit.text()
        if not pattern:
            self.folder_preview_text.setPlainText("パターンを入力してください")
            return

        # サンプルデータでプレビュー生成
        examples = [
            "写真/2023/10/27",
            "動画/2023/10/28",
            "RAW/2023/10/29",
            "Canon EOS R5/2023-10",
            "イベント/2023/Japan/Tokyo",
        ]

        self.folder_preview_text.setPlainText("\n".join(examples))

    def _update_filename_preview(self):
        """ファイル名プレビューを更新"""
        if not self.enable_rename_check.isChecked():
            self.filename_preview_text.setPlainText("ファイル名変更が無効です")
            return

        pattern = self.filename_pattern_edit.text()
        if not pattern:
            self.filename_preview_text.setPlainText("パターンを入力してください")
            return

        # サンプルでプレビュー生成
        examples = [
            "20231027_143000_001.jpg",
            "20231027_143001_002.mp4",
            "Canon_EOS_R5_20231027_IMG_001.cr3",
        ]

        self.filename_preview_text.setPlainText("\n".join(examples))

    def _insert_variable(self, item: QTreeWidgetItem):
        """変数をフォルダパターンに挿入"""
        if item.parent():  # 子アイテムの場合
            text = item.text(0)
            # 変数部分のみを抽出
            if " - " in text:
                variable = text.split(" - ")[0]
                current_text = self.folder_pattern_edit.text()
                cursor_pos = self.folder_pattern_edit.cursorPosition()

                new_text = (
                    current_text[:cursor_pos] + variable + current_text[cursor_pos:]
                )
                self.folder_pattern_edit.setText(new_text)
                self.folder_pattern_edit.setCursorPosition(cursor_pos + len(variable))

    def _validate_preset_name(self):
        """プリセット名を検証"""
        name = self.preset_name_edit.text().strip()

        # 保存ボタンの有効/無効
        self.save_btn.setEnabled(len(name) > 0)

    def _load_from_template(self):
        """テンプレートから設定を読み込み"""
        templates = [
            "旅行写真用",
            "イベント動画用",
            "RAW写真管理用",
            "日常写真用",
            "プロ向け設定",
        ]

        template, ok = QInputDialog.getItem(
            self,
            "テンプレート選択",
            "テンプレートを選択してください:",
            templates,
            0,
            False,
        )

        if ok and template:
            # テンプレート設定を適用
            if template == "旅行写真用":
                self.folder_pattern_edit.setText("{撮影年}/{GPS国}/{GPS都道府県}")
                self.enable_rename_check.setChecked(True)
                self.filename_pattern_edit.setText("{撮影年月日}_{時分秒}_{連番3桁}")
            elif template == "イベント動画用":
                self.folder_pattern_edit.setText("イベント/{撮影年}/{撮影月}/{撮影日}")
                self.enable_rename_check.setChecked(True)
                self.filename_pattern_edit.setText("Event_{撮影年月日}_{連番3桁}")
            # 他のテンプレートも同様に設定

            self._update_folder_preview()
            self._update_filename_preview()

    def _update_preview(self):
        """プレビューを更新"""
        preview_text = "=== プリセット設定プレビュー ===\n\n"

        # フォルダ構造
        preview_text += "【フォルダ構造】\n"
        preview_text += f"パターン: {self.folder_pattern_edit.text()}\n"
        preview_text += "プレビュー:\n"
        preview_text += "  写真/2023/10/27/\n"
        preview_text += "  動画/2023/10/27/\n\n"

        # ファイル名規則
        preview_text += "【ファイル名規則】\n"
        if self.enable_rename_check.isChecked():
            preview_text += f"パターン: {self.filename_pattern_edit.text()}\n"
            preview_text += "プレビュー:\n"
            preview_text += "  20231027_143000_001.jpg\n"
            preview_text += "  20231027_143001_002.mp4\n"
        else:
            preview_text += "ファイル名変更無効（元のファイル名を保持）\n"

        preview_text += "\n"

        # フィルタ設定
        preview_text += "【フィルタ設定】\n"
        file_types = []
        if self.include_photos_check.isChecked():
            file_types.append("写真")
        if self.include_videos_check.isChecked():
            file_types.append("動画")
        if self.include_raw_check.isChecked():
            file_types.append("RAW")
        if self.include_others_check.isChecked():
            file_types.append("その他")

        preview_text += f"対象ファイル: {', '.join(file_types)}\n\n"

        # 処理オプション
        preview_text += "【処理オプション】\n"
        duplicate_options = ["スキップ", "上書き", "名前変更", "確認"]
        selected_duplicate = self.duplicate_button_group.checkedId()
        if selected_duplicate >= 0:
            preview_text += f"重複処理: {duplicate_options[selected_duplicate]}\n"

        preview_text += f"関連ファイル: {'コピーする' if self.copy_related_check.isChecked() else 'コピーしない'}\n"
        preview_text += f"ハッシュ計算: {'有効' if self.calculate_hash_check.isChecked() else '無効'}\n"

        self.preview_text.setPlainText(preview_text)

    def _save_preset(self):
        """プリセットを保存"""
        name = self.preset_name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "エラー", "プリセット名を入力してください。")
            return

        # 設定データを収集
        preset_data = {
            "folder_structure": {
                "pattern": self.folder_pattern_edit.text(),
                "create_subfolder": self.create_subfolder_check.isChecked(),
                "preserve_structure": self.preserve_structure_check.isChecked(),
                "unknown_handling": self.unknown_handling_combo.currentText(),
            },
            "filename_rules": {
                "enabled": self.enable_rename_check.isChecked(),
                "pattern": self.filename_pattern_edit.text(),
                "counter_start": self.counter_start_spin.value(),
                "counter_reset": self.counter_reset_combo.currentText(),
                "duplicate_handling": self.duplicate_handling_combo.currentText(),
                "case_handling": self.case_handling_combo.currentText(),
            },
            "filters": {
                "include_photos": self.include_photos_check.isChecked(),
                "include_videos": self.include_videos_check.isChecked(),
                "include_raw": self.include_raw_check.isChecked(),
                "include_others": self.include_others_check.isChecked(),
                "custom_extensions": self.custom_extensions_edit.text(),
                "size_filter_enabled": self.enable_size_filter_check.isChecked(),
                "min_size": self.min_size_spin.value(),
                "max_size": self.max_size_spin.value(),
                "date_filter_enabled": self.enable_date_filter_check.isChecked(),
            },
            "processing_options": {
                "duplicate_handling": self.duplicate_button_group.checkedId(),
                "copy_related": self.copy_related_check.isChecked(),
                "related_extensions": self.related_extensions_edit.text(),
                "parallel_count": self.parallel_count_spin.value(),
                "calculate_hash": self.calculate_hash_check.isChecked(),
                "extract_metadata": self.extract_metadata_check.isChecked(),
            },
        }

        try:
            # プリセットを保存
            # TODO: 実際の保存処理を実装
            QMessageBox.information(
                self, "成功", f"プリセット「{name}」を保存しました。"
            )
            self.preset_saved.emit(name)
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "エラー", f"プリセットの保存に失敗しました:\n{str(e)}"
            )

    def _load_preset_data(self):
        """プリセットデータを読み込み"""
        if not self.is_new_preset:
            # 既存プリセットの場合、データを読み込み
            # TODO: 実際の読み込み処理を実装
            pass

    def _apply_styling(self):
        """スタイリングを適用"""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2d2d30;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
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
            QPushButton:default {
                background-color: #0e639c;
            }
            QPushButton:default:hover {
                background-color: #1177bb;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #0e639c;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
            }
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3e3e42;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0e639c;
            }
            QCheckBox, QRadioButton {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e42;
                background-color: #2d2d30;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
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
                background-color: #4a4a4a;
            }
        """
        )


def main():
    """テスト用メイン関数"""
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = PresetManagementDialog()
    dialog.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
