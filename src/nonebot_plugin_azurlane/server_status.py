"""区服列表与状态：上游 AzurLaneServerStatus（server-checker.nanoda.work）。

返回的服务器 id 是游戏协议原生纯序号，对接 le3-api 时需要换算。
"""

from typing import Any, TypedDict, cast

import httpx

STATUS_API = "https://server-checker.nanoda.work/api/v1/status"

# 地区 key -> le3-api server_id 前缀（渠道服 le3-api 无数据，不可用）。
_PREFIX: dict[str, int] = {
    "cn": 100,
    "cn_ios": 200,
}

# 渠道服 le3-api 不支持，仅用于 UI 展示（选择后提示失败）。
CHANNEL_KEYS = {"cn_channel"}


class Server(TypedDict):
    """单个服务器条目（id 为游戏协议纯序号）。"""

    key: str
    region_name: str
    name: str
    id: int
    status: str


class ServerStatusError(Exception):
    """区服状态拉取失败。"""


async def fetch_servers(timeout: float = 10) -> list[Server]:
    """拉取全部地区服务器明细，返回规范化的 [{key, name, id, status}] 列表。

    id 为游戏协议纯序号；cn_channel 标记 unsupported。
    """
    async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
        resp = await client.get(STATUS_API)
    resp.raise_for_status()
    data = cast(dict[str, Any], resp.json())
    raw_regions: list[dict[str, Any]] = data.get("regions") or []
    servers: list[Server] = []

    for region in raw_regions:
        key = region.get("key")
        if not isinstance(key, str):
            continue
        region_name = region.get("name") or ""
        raw_servers: list[dict[str, Any]] = region.get("servers") or []
        for sv in raw_servers:
            name = sv.get("name")
            sv_id = sv.get("id")
            status = sv.get("status")
            if not isinstance(name, str) or not isinstance(sv_id, int):
                continue
            servers.append(
                Server(
                    key=key,
                    region_name=region_name,
                    name=name,
                    id=sv_id,
                    status=status if isinstance(status, str) else "unknown",
                )
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


def server_label(sv: Server) -> str:
    """区服展示文案（不含地区 key，避免泄露内部信息）。"""
    if sv["key"] in CHANNEL_KEYS:
        return f"{sv['name']}（渠道服）"
    return sv["name"]
