# 動画・写真コピーユーティリティ

カメラやスマートフォンで撮影された動画および関連ファイル（写真、メタデータファイルなど）を、
ユーザーが定義したルールに基づいて指定のフォルダに整理・コピーするためのユーティリティツールです。

## 主な機能

- **クロスプラットフォーム対応**: WindowsおよびmacOSで動作します。
- **柔軟な整理ルール**: 撮影年月日、使用機材、任意のメタデータなどを基に、カスタマイズ可能なフォルダ階層を生成してコピーします。
- **重複ファイル検知**: ファイルのハッシュ値を比較し、既にコピー先に存在する同一ファイルをスキップまたは通知します。
- **ファイル名変更機能**: コピー時にファイル名を指定のルールに基づいて変更します。
- **関連ファイルの自動コピー**: 動画ファイルに付随するメタデータファイルなどを一緒にコピーします。
- **CUIとGUIの両方に対応**: コマンドラインからのバッチ処理や、直感的なGUIでの操作が可能です。

## インストール方法

### 前提条件

- Python 3.8以上が必要です。

### インストール手順

1. リポジトリをクローンまたはダウンロードします。

```bash
git clone https://github.com/yourusername/video-copy-tool.git
cd video-copy-tool
```

2. 仮想環境を作成して有効化します。

Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. 必要なパッケージをインストールします。

```bash
pip install -r requirements.txt
```

## 使用方法

### GUIモード

GUIモードでアプリケーションを起動するには：

```bash
python run.py --gui
```

または

```bash
python -m src --gui
```

### CLIモード

コマンドラインからツールを使用するには：

```bash
python run.py --source "コピー元フォルダ" --destination "コピー先フォルダ" [オプション]
```

または

```bash
python -m src --source "コピー元フォルダ" --destination "コピー先フォルダ" [オプション]
```

#### 主なコマンドラインオプション

- `--source PATH`, `-s PATH`: コピー元フォルダのパス
- `--destination PATH`, `-d PATH`: コピー先フォルダのパス
- `--preset NAME`, `-p NAME`: 使用するプリセット名
- `--config PATH`, `-c PATH`: 設定ファイルのパス
- `--folder-structure JSON`: フォルダ構造の定義（JSON形式）
- `--filename-pattern JSON`: ファイル名のパターン（JSON形式）
- `--duplicate-handling MODE`: 重複処理モード（skip/overwrite/rename/ask）
- `--dry-run`: 実際にファイルをコピーせずシミュレーション実行
- `--recursive`, `-r`: サブディレクトリも含めて処理（デフォルト有効）
- `--yes`, `-y`: すべての確認プロンプトに自動的にYesと回答

## 設定ファイル

設定ファイルはJSON形式で、プリセットやグローバル設定を保存します。
デフォルトでは `~/.video_copy_tool/config.json` に保存されます。

### 設定例

```json
{
  "version": "1.0",
  "presets": [
    {
      "name": "MyVacationPreset",
      "source": "/Users/username/Pictures/VacationPhotos",
      "destination": "/Users/username/Pictures/Vacations",
      "folderStructure": [
        {"type": "literal", "value": "Events"},
        {"type": "metadata", "value": "year"},
        {"type": "metadata", "value": "month"},
        {"type": "metadata", "value": "day"}
      ],
      "fileNamePattern": [
        {"type": "metadata", "value": "datetime"},
        {"type": "literal", "value": "_"},
        {"type": "original_filename"}
      ],
      "duplicateHandling": "rename",
      "includeAssociatedFiles": true,
      "associatedFileExtensions": ["xmp", "thm", "aae"]
    }
  ],
  "globalSettings": {
    "defaultSource": "",
    "defaultDestination": "",
    "hashAlgorithm": "sha256",
    "cacheHashes": true
  }
}
```

## ライセンス

MITライセンスの下で公開されています。詳細は`LICENSE`ファイルを参照してください。 