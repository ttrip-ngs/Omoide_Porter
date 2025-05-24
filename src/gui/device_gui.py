import logging
import os
import sys
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# 親ディレクトリをパスに追加して相対インポートを可能にする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.device_manager import DeviceManager
from core.file_operations import FileOperations
from core.models import ConnectionStatus, DeviceInfo, DeviceType, SourceType


class DeviceWorkerThread(QThread):
    """デバイス操作用のワーカースレッド"""

    progress_update = Signal(int, int, str)
    operation_complete = Signal(bool, str)
    log_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.device = None
        self.destination = ""
        self.operation = ""

    def configure_device_scan(self, device: DeviceInfo):
        """デバイススキャン用の設定"""
        self.device = device
        self.operation = "scan"

    def configure_device_copy(self, device: DeviceInfo, destination: str):
        """デバイスコピー用の設定"""
        self.device = device
        self.destination = destination
        self.operation = "copy"

    def run(self):
        """スレッドの実行"""
        try:
            if self.operation == "scan":
                self._scan_device()
            elif self.operation == "copy":
                self._copy_from_device()
        except Exception as e:
            self.log_message.emit(f"エラーが発生しました: {str(e)}")
            self.operation_complete.emit(False, str(e))

    def _scan_device(self):
        """デバイスからファイルをスキャン"""
        if not self.device or not self.device.available_paths:
            self.log_message.emit("デバイスのパスが利用できません")
            self.operation_complete.emit(False, "デバイスのパスが利用できません")
            return

        # 利用可能なパスからファイルをスキャン
        all_files = []
        for path in self.device.available_paths:
            self.log_message.emit(f"スキャン中: {path}")
            try:
                files = FileOperations.scan_directory(path, recursive=True)
                all_files.extend(files)
                self.log_message.emit(f"{len(files)}ファイルを発見: {path}")
            except Exception as e:
                self.log_message.emit(f"スキャンエラー: {path} - {str(e)}")

        self.log_message.emit(f"スキャン完了: 合計{len(all_files)}ファイル")
        self.operation_complete.emit(True, f"{len(all_files)}ファイルを発見しました")

    def _copy_from_device(self):
        """デバイスからファイルをコピー"""
        # 実装は通常のファイルコピーと同様
        # デバイス固有の処理があれば追加
        self.log_message.emit("デバイスからのコピー機能は準備中です")
        self.operation_complete.emit(True, "準備中")


class DeviceConnectionWidget(QMainWindow):
    """デバイス接続機能付きのメインウィンドウ"""

    def __init__(self):
        super().__init__()

        self.device_manager = DeviceManager()
        self.connected_devices = []
        self.selected_device = None
        self.worker_thread = DeviceWorkerThread()
        self.config_manager = ConfigManager()

        self._setup_ui()
        self._connect_signals()
        self._start_device_monitoring()

    def _setup_ui(self):
        """UIを設定"""
        self.setWindowTitle("動画・写真コピーユーティリティ - デバイス接続")
        self.resize(900, 700)

        # メインレイアウト
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # タブウィジェット
        self.tab_widget = QTabWidget()

        # デバイス接続タブ
        device_tab = self._create_device_tab()
        self.tab_widget.addTab(device_tab, "デバイス接続")

        # ファイル操作タブ
        file_tab = self._create_file_tab()
        self.tab_widget.addTab(file_tab, "ファイル操作")

        # ログタブ
        log_tab = self._create_log_tab()
        self.tab_widget.addTab(log_tab, "ログ")

        main_layout.addWidget(self.tab_widget)

        # ステータスバー
        self.statusBar().showMessage("準備完了")

    def _create_device_tab(self) -> QWidget:
        """デバイスタブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # デバイス検出ボタン
        detect_layout = QHBoxLayout()
        self.detect_button = QPushButton("デバイス検出")
        self.detect_button.setMinimumHeight(40)
        detect_layout.addWidget(self.detect_button)
        detect_layout.addStretch()
        layout.addLayout(detect_layout)

        # デバイスリスト
        device_group = QGroupBox("接続されたデバイス")
        device_layout = QVBoxLayout(device_group)

        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(200)
        device_layout.addWidget(self.device_list)

        layout.addWidget(device_group)

        # デバイス詳細情報
        info_group = QGroupBox("デバイス情報")
        info_layout = QVBoxLayout(info_group)

        self.device_info_text = QTextEdit()
        self.device_info_text.setReadOnly(True)
        self.device_info_text.setMaximumHeight(150)
        self.device_info_text.setText("デバイスを選択してください")
        info_layout.addWidget(self.device_info_text)

        layout.addWidget(info_group)

        # コピー先設定
        dest_group = QGroupBox("コピー先設定")
        dest_layout = QVBoxLayout(dest_group)

        dest_select_layout = QHBoxLayout()
        dest_select_layout.addWidget(QLabel("コピー先:"))
        self.dest_edit = QLineEdit()
        dest_select_layout.addWidget(self.dest_edit)
        self.dest_browse_button = QPushButton("参照...")
        dest_select_layout.addWidget(self.dest_browse_button)
        dest_layout.addLayout(dest_select_layout)

        layout.addWidget(dest_group)

        # 実行ボタン
        action_layout = QHBoxLayout()
        self.scan_device_button = QPushButton("デバイスをスキャン")
        self.scan_device_button.setEnabled(False)
        action_layout.addWidget(self.scan_device_button)

        self.copy_from_device_button = QPushButton("デバイスからコピー")
        self.copy_from_device_button.setEnabled(False)
        action_layout.addWidget(self.copy_from_device_button)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        return widget

    def _create_file_tab(self) -> QWidget:
        """ファイル操作タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ファイルリスト
        file_group = QGroupBox("検出されたファイル")
        file_layout = QVBoxLayout(file_group)

        self.file_list = QListWidget()
        file_layout.addWidget(self.file_list)

        layout.addWidget(file_group)

        # 進捗バー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return widget

    def _create_log_tab(self) -> QWidget:
        """ログタブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # ログクリアボタン
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        self.clear_log_button = QPushButton("ログをクリア")
        clear_layout.addWidget(self.clear_log_button)
        layout.addLayout(clear_layout)

        return widget

    def _connect_signals(self):
        """シグナルを接続"""
        # デバイス関連
        self.detect_button.clicked.connect(self._detect_devices)
        self.device_list.itemSelectionChanged.connect(self._device_selection_changed)
        self.dest_browse_button.clicked.connect(self._browse_destination)
        self.scan_device_button.clicked.connect(self._scan_device)
        self.copy_from_device_button.clicked.connect(self._copy_from_device)

        # ログ関連
        self.clear_log_button.clicked.connect(self._clear_log)

        # ワーカースレッド
        self.worker_thread.progress_update.connect(self._update_progress)
        self.worker_thread.operation_complete.connect(self._operation_complete)
        self.worker_thread.log_message.connect(self._log_message)

    def _start_device_monitoring(self):
        """デバイス監視を開始"""
        # デバイス変更コールバックを設定
        self.device_manager.add_device_change_callback(self._on_devices_changed)

        # 初回デバイス検出
        self._detect_devices()

        # 定期監視タイマー（10秒間隔）
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._detect_devices)
        self.monitor_timer.start(10000)

    def _detect_devices(self):
        """デバイスを検出"""
        try:
            self.connected_devices = self.device_manager.scan_devices()
            self._update_device_list()
            self._log_message(f"デバイス検出完了: {len(self.connected_devices)}台発見")
            self.statusBar().showMessage(
                f"デバイス検出完了: {len(self.connected_devices)}台"
            )
        except Exception as e:
            self._log_message(f"デバイス検出エラー: {str(e)}")
            self.statusBar().showMessage("デバイス検出エラー")

    def _update_device_list(self):
        """デバイスリストを更新"""
        self.device_list.clear()

        for device in self.connected_devices:
            # デバイスタイプに応じたアイコン
            if device.device_type == DeviceType.IOS:
                icon = "📱"
            elif device.device_type == DeviceType.ANDROID:
                icon = "🤖"
            elif device.device_type == DeviceType.CAMERA:
                icon = "📷"
            else:
                icon = "❓"

            # 接続状態の表示
            status = ""
            if device.connection_status == ConnectionStatus.CONNECTED:
                status = " ✅"
            elif device.connection_status == ConnectionStatus.AUTHENTICATING:
                status = " 🔒"
            elif device.connection_status == ConnectionStatus.ERROR:
                status = " ❌"

            display_text = f"{icon} {device.display_name}{status}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, device)
            self.device_list.addItem(item)

    def _device_selection_changed(self):
        """デバイス選択変更時の処理"""
        selected_items = self.device_list.selectedItems()
        if not selected_items:
            self.selected_device = None
            self.device_info_text.setText("デバイスを選択してください")
            self.scan_device_button.setEnabled(False)
            self.copy_from_device_button.setEnabled(False)
            return

        self.selected_device = selected_items[0].data(Qt.UserRole)
        self._update_device_info()

        # ボタンの有効化
        can_operate = (
            self.selected_device.connection_status == ConnectionStatus.CONNECTED
            and bool(self.selected_device.available_paths)
        )
        self.scan_device_button.setEnabled(can_operate)
        self.copy_from_device_button.setEnabled(
            can_operate and bool(self.dest_edit.text())
        )

    def _update_device_info(self):
        """デバイス情報を更新"""
        if not self.selected_device:
            return

        device = self.selected_device
        info_text = f"""デバイス名: {device.display_name}
タイプ: {device.device_type.value}
メーカー: {device.manufacturer or "不明"}
モデル: {device.model or "不明"}
プロトコル: {device.protocol.value}
接続状態: {device.connection_status.value}
"""

        if device.total_capacity > 0:
            info_text += f"容量: {device.capacity_gb:.1f} GB\n"
            info_text += f"空き容量: {device.free_space_gb:.1f} GB\n"
            info_text += f"使用率: {device.used_space_percent:.1f}%\n"

        if device.available_paths:
            info_text += f"\n利用可能パス:\n"
            for path in device.available_paths:
                info_text += f"  • {path}\n"

        self.device_info_text.setText(info_text)

    def _browse_destination(self):
        """コピー先フォルダを選択"""
        folder = QFileDialog.getExistingDirectory(self, "コピー先フォルダを選択")
        if folder:
            self.dest_edit.setText(folder)
            # コピーボタンの有効化をチェック
            self._device_selection_changed()

    def _scan_device(self):
        """デバイスをスキャン"""
        if not self.selected_device:
            return

        self.progress_bar.setVisible(True)
        self.scan_device_button.setEnabled(False)

        self.worker_thread.configure_device_scan(self.selected_device)
        self.worker_thread.start()

    def _copy_from_device(self):
        """デバイスからコピー"""
        if not self.selected_device or not self.dest_edit.text():
            QMessageBox.warning(self, "エラー", "デバイスとコピー先を選択してください")
            return

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"デバイス '{self.selected_device.display_name}' から\n"
            f"'{self.dest_edit.text()}' にファイルをコピーしますか？",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.No:
            return

        self.progress_bar.setVisible(True)
        self.copy_from_device_button.setEnabled(False)

        self.worker_thread.configure_device_copy(
            self.selected_device, self.dest_edit.text()
        )
        self.worker_thread.start()

    def _clear_log(self):
        """ログをクリア"""
        self.log_text.clear()

    def _on_devices_changed(self, devices: List[DeviceInfo]):
        """デバイス変更コールバック"""
        self.connected_devices = devices
        self._update_device_list()
        self._log_message(f"デバイス変更検出: {len(devices)}台")

    @Slot(int, int, str)
    def _update_progress(self, current: int, total: int, filename: str):
        """進捗更新"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"%v/%m (%p%) - {filename}")

    @Slot(bool, str)
    def _operation_complete(self, success: bool, message: str):
        """操作完了"""
        self.progress_bar.setVisible(False)
        self.scan_device_button.setEnabled(True)
        self.copy_from_device_button.setEnabled(True)

        if success:
            QMessageBox.information(self, "完了", message)
        else:
            QMessageBox.warning(self, "エラー", message)

        self.statusBar().showMessage("準備完了")

    @Slot(str)
    def _log_message(self, message: str):
        """ログメッセージを追加"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # 自動スクロール
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)


def main():
    """メイン関数"""
    app = QApplication(sys.argv)

    # ログ設定
    logging.basicConfig(level=logging.INFO)

    window = DeviceConnectionWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
