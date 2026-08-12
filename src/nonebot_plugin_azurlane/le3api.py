"""le3-api 客户端：B 站碧蓝航线微信小程序后端接口（逆向 + 模拟调用）。"""

import httpx

from .types import (
    JsonObj,
    UserDetail,
    BuildRecordItem,
    BuildRecordResult,
)

BASE_URL = "https://le3-api.game.bilibili.com/x/api/azurlane"
GAME_ID = "182"

# 直连（trust_env=False），避免被本机系统代理劫持导致 TLS 失败。
_TIMEOUT = httpx.Timeout(15)

# 伪装成微信小程序客户端，缺少会被接口拒绝。
HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 "
        "MicroMessenger/7.0.20.1781"
    ),
    "Referer": "https://servicewechat.com/wx3ee6dc49667f3444/26/page-frame.html",
    "Content-Type": "application/json",
}


class APIError(Exception):
    """接口业务错误，message 为可展示文案。"""


def _build_headers(cookie: str | None) -> dict[str, str]:
    """构造请求头，可选附加 Cookie。"""
    headers: dict[str, str] = dict(HEADERS)
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _envelope_check(data: JsonObj) -> JsonObj:
    """校验统一响应信封；code != 0 直接抛错。"""
    code = data.get("code")
    if code != 0:
        raise APIError(data.get("message") or f"接口错误（code={code}）")
    raw = data.get("data")
    if not isinstance(raw, dict):
        raise APIError("接口返回数据格式异常")
    return raw


async def get_user_detail(role_id: str, server_id: str, cookie: str | None = None) -> UserDetail:
    """指挥官详情 get/user_detail。"""
    params: dict[str, str] = {
        "role_id": role_id,
        "server_id": server_id,
        "game_id": GAME_ID,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        resp = await client.get(
            f"{BASE_URL}/get/user_detail",
            params=params,
            headers=_build_headers(cookie),
        )
    resp.raise_for_status()
    return _envelope_check(resp.json())  # type: ignore[return-value]


async def get_build_record(
    role_id: str,
    server_id: str,
    target_count: int = 10,
    cookie: str | None = None,
) -> BuildRecordResult:
    """建造记录 get/build_record，按每页最多 50 条循环拉取凑够 target_count。

    分页约定：最后一页 page_size 取剩余量；任一页非 0 即中断。
    """
    target_count = max(1, min(target_count, 500))
    records: list[BuildRecordItem] = []
    page_num = 1
    remaining = target_count
    page_size = min(remaining, 50)
    nickname: str | None = None
    uid: str | None = None
    server_name: str | None = None
    avatar: str | None = None
    total_count = 0

    async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
        while remaining > 0:
            params: dict[str, str] = {
                "role_id": role_id,
                "server_id": server_id,
                "page_num": str(page_num),
                "page_size": str(page_size),
            }
            resp = await client.get(
                f"{BASE_URL}/get/build_record",
                params=params,
                headers=_build_headers(cookie),
            )
            resp.raise_for_status()
            data = _envelope_check(resp.json())

            nickname = data.get("nickname", nickname)  # type: ignore[assignment]
            uid = data.get("uid", uid)  # type: ignore[assignment]
            server_name = data.get("serverName", server_name)  # type: ignore[assignment]
            avatar = data.get("avatar", avatar)  # type: ignore[assignment]

            build_records = data.get("buildRecords")
            if isinstance(build_records, dict):
                total = build_records.get("total_count")
                if isinstance(total, int):
                    total_count = total
                page = build_records.get("data")
            else:
                page = None

            if not isinstance(page, list):
                break
            records.extend(page)  # type: ignore[arg-type]
            remaining -= len(page)
            if remaining <= 0:
                break
            page_num += 1
            page_size = min(remaining, 50)

    return BuildRecordResult(
        nickname=nickname,
        uid=uid,
        server_name=server_name,
        avatar=avatar,
        total_count=total_count,
        records=records,
    )
