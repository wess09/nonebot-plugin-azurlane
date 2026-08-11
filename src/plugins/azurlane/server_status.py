"""区服列表与状态：上游 AzurLaneServerStatus（server-checker.nanoda.work）。

返回的服务器 id 是游戏协议原生纯序号，对接 le3-api 时需要换算（API.md 第 4 节）。
"""

import httpx

STATUS_API = "https://server-checker.nanoda.work/api/v1/status"

# 地区 key -> le3-api server_id 前缀（渠道服 le3-api 无数据，不可用）
_PREFIX = {
    "cn": 100,
    "cn_ios": 200,
}

# 渠道服 le3-api 不支持，仅用于 UI 展示（选择后提示失败）
CHANNEL_KEYS = {"cn_channel"}


class ServerStatusError(Exception):
    """区服状态拉取失败。"""


def fetch_servers(timeout: float = 10) -> list[dict]:
    """拉取全部地区服务器明细，返回规范化的 [{key, name, id, status}] 列表。

    id 为游戏协议纯序号；cn_channel 标记 unsupported。
    """
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        resp = client.get(STATUS_API)
    resp.raise_for_status()
    data = resp.json()
    regions = data.get("regions") or []

    servers = []
    for region in regions:
        key = region.get("key")
        for sv in region.get("servers") or []:
            servers.append(
                {
                    "key": key,
                    "region_name": region.get("name"),
                    "name": sv.get("name"),
                    "id": sv.get("id"),
                    "status": sv.get("status"),
                }
            )
    return servers


def server_id_for(key: str, id: int) -> int | None:
    """游戏协议纯序号 -> le3-api server_id；渠道服返回 None。"""
    if key in CHANNEL_KEYS:
        return None
    prefix = _PREFIX.get(key)
    if prefix is None:
        return None
    return prefix + id


def server_label(sv: dict) -> str:
    """区服展示文案（不含地区 key，避免泄露内部信息）。"""
    if sv.get("key") in CHANNEL_KEYS:
        return f"{sv['name']}（渠道服）"
    return sv["name"]
