"""
デバイス関連のCLIコマンド
"""

import click
from tabulate import tabulate
from typing import Optional

from loguru import logger

from ..core.device_manager import DeviceManager
from ..core.models import DeviceType, ConnectionStatus


@click.group()
def device():
    """デバイス関連のコマンド"""
    pass


@device.command("list")
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table", help="出力形式")
@click.option("--verbose", "-v", is_flag=True, help="詳細情報を表示")
def list_devices(format: str, verbose: bool):
    """接続されたデバイス一覧を表示"""
    try:
        device_manager = DeviceManager()
        devices = device_manager.scan_devices()
        
        if not devices:
            click.echo("接続されたデバイスが見つかりませんでした。")
            return
        
        if format == "json":
            import json
            device_data = [device.to_dict() for device in devices]
            click.echo(json.dumps(device_data, indent=2, ensure_ascii=False))
            
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = ["device_id", "device_type", "display_name", "manufacturer", "model", "connection_status"]
            if verbose:
                fieldnames.extend(["protocol", "capacity_gb", "free_space_gb", "transfer_speed"])
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for device in devices:
                row = {
                    "device_id": device.device_id,
                    "device_type": device.device_type.value,
                    "display_name": device.display_name,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "connection_status": device.connection_status.value
                }
                if verbose:
                    row.update({
                        "protocol": device.protocol.value,
                        "capacity_gb": f"{device.capacity_gb:.1f}",
                        "free_space_gb": f"{device.free_space_gb:.1f}",
                        "transfer_speed": f"{device.transfer_speed:.1f}"
                    })
                writer.writerow(row)
            
            click.echo(output.getvalue())
            
        else:  # table format
            headers = ["ID", "タイプ", "デバイス名", "メーカー", "ステータス"]
            rows = []
            
            if verbose:
                headers.extend(["プロトコル", "容量(GB)", "空き(GB)", "速度(MB/s)"])
            
            for device in devices:
                row = [
                    device.device_id[:12] + "..." if len(device.device_id) > 15 else device.device_id,
                    device.device_type.value,
                    device.display_name,
                    device.manufacturer,
                    _get_status_display(device.connection_status)
                ]
                
                if verbose:
                    row.extend([
                        device.protocol.value,
                        f"{device.capacity_gb:.1f}",
                        f"{device.free_space_gb:.1f}",
                        f"{device.transfer_speed:.1f}"
                    ])
                
                rows.append(row)
            
            click.echo(f"\n検出されたデバイス: {len(devices)}個")
            click.echo(tabulate(rows, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        logger.error(f"デバイス一覧表示エラー: {e}")
        click.echo(f"エラー: {e}", err=True)
        raise click.Abort()


@device.command("info")
@click.argument("device_id")
def device_info(device_id: str):
    """指定されたデバイスの詳細情報を表示"""
    try:
        device_manager = DeviceManager()
        devices = device_manager.scan_devices()
        
        # デバイスIDの部分マッチも許可
        target_device = None
        for device in devices:
            if device.device_id == device_id or device.device_id.startswith(device_id):
                target_device = device
                break
        
        if not target_device:
            click.echo(f"デバイスID '{device_id}' が見つかりませんでした。", err=True)
            click.echo("使用可能なデバイス一覧を確認するには 'device list' を実行してください。")
            raise click.Abort()
        
        # デバイス詳細情報を表示
        click.echo(f"\n=== デバイス詳細情報 ===")
        click.echo(f"デバイスID: {target_device.device_id}")
        click.echo(f"デバイス名: {target_device.display_name}")
        click.echo(f"タイプ: {target_device.device_type.value}")
        click.echo(f"メーカー: {target_device.manufacturer}")
        click.echo(f"モデル: {target_device.model}")
        click.echo(f"シリアル番号: {target_device.serial_number}")
        click.echo(f"プロトコル: {target_device.protocol.value}")
        click.echo(f"接続パス: {target_device.connection_path}")
        click.echo(f"認証状態: {'認証済み' if target_device.is_authenticated else '未認証'}")
        click.echo(f"接続状態: {_get_status_display(target_device.connection_status)}")
        
        if target_device.total_capacity > 0:
            click.echo(f"\n=== ストレージ情報 ===")
            click.echo(f"総容量: {target_device.capacity_gb:.1f} GB")
            click.echo(f"空き容量: {target_device.free_space_gb:.1f} GB")
            click.echo(f"使用率: {target_device.used_space_percent:.1f}%")
        
        if target_device.available_paths:
            click.echo(f"\n=== 利用可能パス ===")
            for path in target_device.available_paths:
                click.echo(f"  {path}")
        
        if target_device.transfer_speed > 0:
            click.echo(f"\n転送速度: {target_device.transfer_speed:.1f} MB/s")
        
        if target_device.last_connected:
            click.echo(f"最終接続: {target_device.last_connected.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"デバイス情報表示エラー: {e}")
        click.echo(f"エラー: {e}", err=True)
        raise click.Abort()


@device.command("scan")
@click.option("--watch", "-w", is_flag=True, help="デバイス変更を監視し続ける")
@click.option("--interval", default=5, help="監視間隔（秒）")
def scan_devices(watch: bool, interval: int):
    """デバイスをスキャンする"""
    try:
        device_manager = DeviceManager()
        
        if watch:
            click.echo(f"デバイス監視を開始します（間隔: {interval}秒）")
            click.echo("Ctrl+Cで停止")
            
            def on_device_change(devices):
                click.clear()
                click.echo(f"[{click.datetime.now().strftime('%H:%M:%S')}] デバイス更新: {len(devices)}個")
                
                if devices:
                    headers = ["タイプ", "デバイス名", "ステータス"]
                    rows = []
                    for device in devices:
                        rows.append([
                            device.device_type.value,
                            device.display_name,
                            _get_status_display(device.connection_status)
                        ])
                    click.echo(tabulate(rows, headers=headers, tablefmt="simple"))
                else:
                    click.echo("接続されたデバイスはありません。")
            
            device_manager.add_device_change_callback(on_device_change)
            
            try:
                device_manager.start_monitoring(interval)
                # 初回スキャン
                initial_devices = device_manager.scan_devices()
                on_device_change(initial_devices)
                
                # 監視継続
                while True:
                    click.pause("")
            except KeyboardInterrupt:
                click.echo("\n監視を停止しました。")
        else:
            devices = device_manager.scan_devices()
            click.echo(f"スキャン完了: {len(devices)}個のデバイスが見つかりました。")
            
            if devices:
                headers = ["ID", "タイプ", "デバイス名", "ステータス"]
                rows = []
                for device in devices:
                    rows.append([
                        device.device_id[:12] + "..." if len(device.device_id) > 15 else device.device_id,
                        device.device_type.value,
                        device.display_name,
                        _get_status_display(device.connection_status)
                    ])
                click.echo(tabulate(rows, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        logger.error(f"デバイススキャンエラー: {e}")
        click.echo(f"エラー: {e}", err=True)
        raise click.Abort()


def _get_status_display(status: ConnectionStatus) -> str:
    """接続状態の表示文字列を取得"""
    status_map = {
        ConnectionStatus.CONNECTED: "✓ 接続",
        ConnectionStatus.DISCONNECTED: "✗ 切断",
        ConnectionStatus.AUTHENTICATING: "🔐 認証中",
        ConnectionStatus.ERROR: "❌ エラー",
        ConnectionStatus.UNKNOWN: "? 不明"
    }
    return status_map.get(status, status.value)


# CLI のメインコマンドに追加用
def add_device_commands(main_cli):
    """メインCLIにデバイスコマンドを追加"""
    main_cli.add_command(device) 