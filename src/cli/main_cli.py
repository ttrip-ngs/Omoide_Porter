#!/usr/bin/env python
"""
動画・写真コピーユーティリティの統合CLIアプリケーション
デバイス機能を含む包括的なインターフェース
"""

import click
import sys
from pathlib import Path

from loguru import logger

from .device_commands import add_device_commands
from ..core.config import ConfigManager
from ..core.device_manager import DeviceManager


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="設定ファイルのパス")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]), 
              default="INFO", help="ログレベル")
@click.pass_context
def cli(ctx, config, log_level):
    """動画・写真コピーユーティリティツール
    
    iPhoneやAndroid、デジタルカメラなどのデバイスから
    写真や動画を効率的に整理・コピーします。
    """
    # ログ設定
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    
    # コンテキストにグローバル設定を保存
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level
    
    # 設定ファイルの読み込み
    config_manager = ConfigManager(Path(config) if config else None)
    ctx.obj["config_manager"] = config_manager
    ctx.obj["config"] = config_manager.load_config()


@cli.command()
@click.option("--source", "-s", help="コピー元フォルダまたはデバイス")
@click.option("--destination", "-d", required=True, help="コピー先フォルダ")
@click.option("--preset", "-p", help="使用するプリセット名")
@click.option("--device", help="使用するデバイス名")
@click.option("--device-id", help="使用するデバイスID")
@click.option("--dry-run", is_flag=True, help="実際にファイルをコピーせず、シミュレーション実行")
@click.option("--yes", "-y", is_flag=True, help="すべての確認プロンプトにYesと答える")
@click.pass_context
def copy(ctx, source, destination, preset, device, device_id, dry_run, yes):
    """ファイルのコピーを実行
    
    ソースとしてフォルダパスまたはデバイスを指定できます。
    デバイスを使用する場合は --device または --device-id オプションを使用してください。
    """
    config_manager = ctx.obj["config_manager"]
    app_config = ctx.obj["config"]
    
    try:
        # プリセットの取得
        if preset:
            preset_config = config_manager.get_preset_by_name(preset)
            if not preset_config:
                click.echo(f"プリセット '{preset}' が見つかりません。", err=True)
                raise click.Abort()
        else:
            preset_config = None
        
        # ソースの決定
        source_path = None
        source_device_info = None
        
        if device or device_id:
            # デバイスからコピー
            device_manager = DeviceManager()
            devices = device_manager.scan_devices()
            
            if not devices:
                click.echo("接続されたデバイスが見つかりません。", err=True)
                raise click.Abort()
            
            # デバイス検索
            target_device = None
            if device_id:
                target_device = device_manager.get_device_by_id(device_id)
            elif device:
                for d in devices:
                    if device.lower() in d.display_name.lower():
                        target_device = d
                        break
            
            if not target_device:
                click.echo(f"指定されたデバイスが見つかりません: {device or device_id}", err=True)
                click.echo("使用可能なデバイス:")
                for d in devices:
                    click.echo(f"  {d.device_id}: {d.display_name}")
                raise click.Abort()
            
            source_device_info = target_device
            # デバイスの場合、利用可能パスから選択
            if target_device.available_paths:
                source_path = target_device.available_paths[0]
            else:
                click.echo(f"デバイス '{target_device.display_name}' にアクセス可能なパスがありません。", err=True)
                raise click.Abort()
        
        elif source:
            # フォルダからコピー
            source_path = source
            if not Path(source_path).exists():
                click.echo(f"コピー元が存在しません: {source_path}", err=True)
                raise click.Abort()
        
        else:
            click.echo("--source または --device/--device-id を指定してください。", err=True)
            raise click.Abort()
        
        # コピー処理の実行
        click.echo(f"コピー元: {source_path}")
        if source_device_info:
            click.echo(f"デバイス: {source_device_info.display_name} ({source_device_info.device_type.value})")
        click.echo(f"コピー先: {destination}")
        
        if dry_run:
            click.echo("🔍 ドライラン実行中...")
        else:
            if not yes:
                if not click.confirm("コピーを実行しますか？"):
                    click.echo("キャンセルしました。")
                    return
        
        # TODO: 実際のコピー処理を実装
        click.echo("コピー処理を実装中です...")
        
    except Exception as e:
        logger.error(f"コピー処理エラー: {e}")
        click.echo(f"エラー: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--format", type=click.Choice(["table", "json"]), default="table", help="出力形式")
def list_presets(format):
    """設定済みプリセット一覧を表示"""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        if not config.presets:
            click.echo("プリセットが設定されていません。")
            return
        
        if format == "json":
            import json
            preset_data = [
                {
                    "name": preset.name,
                    "destination": preset.destination,
                    "duplicate_handling": preset.duplicate_handling.value
                }
                for preset in config.presets
            ]
            click.echo(json.dumps(preset_data, indent=2, ensure_ascii=False))
        else:
            from tabulate import tabulate
            
            headers = ["プリセット名", "出力先", "重複処理"]
            rows = []
            for preset in config.presets:
                rows.append([
                    preset.name,
                    preset.destination,
                    preset.duplicate_handling.value
                ])
            
            click.echo(tabulate(rows, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        logger.error(f"プリセット一覧表示エラー: {e}")
        click.echo(f"エラー: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("preset_name")
def show_preset(preset_name):
    """指定されたプリセットの詳細を表示"""
    try:
        config_manager = ConfigManager()
        preset = config_manager.get_preset_by_name(preset_name)
        
        if not preset:
            click.echo(f"プリセット '{preset_name}' が見つかりません。", err=True)
            raise click.Abort()
        
        click.echo(f"\n=== プリセット: {preset.name} ===")
        click.echo(f"出力先: {preset.destination}")
        click.echo(f"重複処理: {preset.duplicate_handling.value}")
        click.echo(f"関連ファイル含む: {'はい' if preset.include_associated_files else 'いいえ'}")
        click.echo(f"ログレベル: {preset.log_level}")
        
        # フォルダ構造
        if preset.folder_structure.levels:
            click.echo(f"\nフォルダ構造:")
            for i, level in enumerate(preset.folder_structure.levels):
                prefix = "  └─ " if i == len(preset.folder_structure.levels) - 1 else "  ├─ "
                if level.type == "literal":
                    click.echo(f"{prefix}{level.value}")
                elif level.type == "metadata":
                    format_str = f" ({level.format})" if level.format else ""
                    click.echo(f"{prefix}{{{level.field}}}{format_str}")
        
        # ファイル名パターン
        if preset.file_name_pattern.components:
            click.echo(f"\nファイル名パターン:")
            pattern_str = ""
            for component in preset.file_name_pattern.components:
                if component.type == "literal":
                    pattern_str += component.value or ""
                elif component.type == "metadata":
                    format_str = f":{component.format}" if component.format else ""
                    pattern_str += f"{{{component.field}{format_str}}}"
                elif component.type == "original_filename":
                    pattern_str += "{original_filename}"
                elif component.type == "original_extension":
                    pattern_str += "{ext}"
            click.echo(f"  {pattern_str}")
        
    except Exception as e:
        logger.error(f"プリセット表示エラー: {e}")
        click.echo(f"エラー: {e}", err=True)
        raise click.Abort()


@cli.command()
def version():
    """バージョン情報を表示"""
    click.echo("Video Copy Tool v1.0.0")
    click.echo("デバイス対応動画・写真コピーユーティリティ")


def main():
    """メインエントリーポイント"""
    # デバイスコマンドを追加
    add_device_commands(cli)
    
    # CLIを実行
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n操作がキャンセルされました。")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 