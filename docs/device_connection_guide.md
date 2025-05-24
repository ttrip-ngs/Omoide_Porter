# ケーブル接続デバイス機能ガイド

## 1. 概要

この機能により、iPhone、iPad、Androidデバイス、デジタルカメラなどをUSBやThunderboltケーブルで直接PC/Macに接続して、効率的にメディアファイルをコピーできます。

## 2. 対応デバイス

### 2.1 iOS デバイス (iPhone/iPad)
- **対応バージョン**: iOS 13.0以降
- **接続方法**: Lightning - USBケーブル、USB-C - USBケーブル
- **プロトコル**: AFC (Apple File Conduit)
- **認証**: 「このコンピューターを信頼」が必要
- **アクセス可能フォルダ**: 
  - `/DCIM/` (Camera Roll)
  - `/PhotoData/` (Live Photosの関連データ)

### 2.2 Android デバイス
- **対応バージョン**: Android 6.0以降
- **接続方法**: USB-C、micro-USBケーブル
- **プロトコル**: MTP (Media Transfer Protocol)
- **認証**: ファイル転送モード選択が必要
- **アクセス可能フォルダ**:
  - `/DCIM/Camera/` (標準カメラアプリ)
  - `/Pictures/` (スクリーンショット等)
  - `/Movies/` (動画ファイル)
  - `/Download/` (ダウンロードファイル)

### 2.3 デジタルカメラ
- **対応規格**: Mass Storage Class (MSC)、PTP (Picture Transfer Protocol)
- **接続方法**: USBケーブル
- **メモリカード**: CF、SD、microSD等
- **アクセス可能フォルダ**:
  - `/DCIM/` (DCF規格準拠)
  - メーカー固有フォルダ (Canon、Nikon、Sony等)

## 3. 接続手順

### 3.1 iOS デバイス
1. iPhoneまたはiPadをUSBケーブルでPCに接続
2. デバイス画面に「このコンピューターを信頼しますか？」が表示されたら「信頼」をタップ
3. アプリケーションで自動的に検出され、デバイス一覧に表示
4. 必要に応じてiTunesまたはApple Mobile Device Supportのインストールが必要

### 3.2 Android デバイス
1. AndroidデバイスをUSBケーブルでPCに接続
2. 通知欄から「USB設定」を開き、「ファイル転送」または「MTP」を選択
3. アプリケーションで自動的に検出され、デバイス一覧に表示

### 3.3 デジタルカメラ
1. カメラの電源を入れ、USBケーブルでPCに接続
2. カメラの設定で「PC連携」または「USB接続」モードに設定
3. アプリケーションで自動的に検出され、デバイス一覧に表示

## 4. 技術仕様

### 4.1 サポートライブラリ

| プラットフォーム | iOS | Android | Camera |
|-----------------|-----|---------|---------|
| **Windows** | pymobiledevice3 | windows-media-format-sdk | libgphoto2 |
| **macOS** | libimobiledevice | libmtp | libgphoto2 |
| **Linux** | libimobiledevice | libmtp | libgphoto2 |

### 4.2 転送性能

| 接続方式 | 理論値 | 実測値(目安) |
|----------|---------|-------------|
| **USB 2.0** | 480 Mbps | 20-30 MB/s |
| **USB 3.0** | 5 Gbps | 100-150 MB/s |
| **USB-C** | 10 Gbps | 200-300 MB/s |
| **Thunderbolt 3** | 40 Gbps | 500+ MB/s |

### 4.3 ファイル形式サポート

| デバイス | 画像 | 動画 | RAW |
|----------|------|------|-----|
| **iPhone** | JPEG, HEIC | MOV, MP4, M4V | DNG |
| **Android** | JPEG, PNG | MP4, 3GP, WEBM | DNG, ARW |
| **Camera** | JPEG | MP4, MOV | CR2, NEF, ARW, DNG |

## 5. トラブルシューティング

### 5.1 デバイスが認識されない

**iPhone/iPad**:
- iTunesまたはApple Mobile Device Supportがインストールされているか確認
- 「このコンピューターを信頼」を再度実行
- Lightningケーブルの接触不良を確認

**Android**:
- USBデバッグをOFFにする
- 「ファイル転送」モードが選択されているか確認
- 異なるUSBポートを試す

**デジタルカメラ**:
- カメラのバッテリー残量を確認
- カメラの「PC連携」モードを確認
- メモリカードが正しく挿入されているか確認

### 5.2 転送速度が遅い

- USB 3.0以上のポートを使用
- 他のUSBデバイスを取り外す
- デバイスの容量に余裕があるか確認
- ウイルススキャンソフトのリアルタイム保護を一時無効化

### 5.3 権限エラー

**Windows**:
- 管理者権限でアプリケーションを実行
- デバイスマネージャーでドライバーを確認

**macOS**:
- システム環境設定 > セキュリティとプライバシー > プライバシー > ファイルとフォルダでアクセス許可
- Gatekeeperの例外設定

**Linux**:
- ユーザーをplugdevグループに追加: `sudo usermod -a -G plugdev $USER`
- udevルールの設定確認

## 6. セキュリティとプライバシー

### 6.1 データ保護
- すべてのファイル操作は読み取り専用
- 一時ファイルやキャッシュは適切に削除
- ファイルのメタデータは最小限のみ取得

### 6.2 プライバシー配慮
- システムフォルダや非公開フォルダには一切アクセスしない
- ユーザーが明示的に選択したフォルダのみスキャン
- GPS位置情報等の個人情報は適切に処理

### 6.3 認証とアクセス制御
- デバイス側での認証・許可が必要なアクセスのみ実行
- 不正アクセス防止のため、認証されていないデバイスは表示しない

## 7. 将来の拡張予定

- **ワイヤレス転送**: WiFi Direct、AirDropサポート
- **クラウド連携**: iCloud Photos、Google Photos直接アクセス
- **デバイス管理**: 複数デバイスの同期・管理機能
- **自動起動**: デバイス接続時の自動アプリ起動
- **高速転送**: USB4、Thunderbolt 4対応 