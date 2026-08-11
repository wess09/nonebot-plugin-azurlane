"""一次性绑定会话：token -> {qq, cb}。

/绑定 指令生成短 token（10 分钟有效），登录 URL 只带 token，不暴露 QQ 与回调信息。
"""

import time
import secrets
from typing import TypedDict


class Session(TypedDict):
    """一个绑定会话：QQ、回调地址与创建时间戳。"""

    qq: str
    cb: str
    created: float


# token -> Session
_sessions: dict[str, Session] = {}
_TTL = 10 * 60  # 10 分钟


def create_session(qq: str, cb: str) -> str:
    """创建绑定会话，返回一次性 token。"""
    token = secrets.token_urlsafe(16)
    _sessions[token] = Session(qq=qq, cb=cb, created=time.time())
    _cleanup()
    return token


def get_session(token: str) -> Session | None:
    """按 token 查询会话，不存在或已过期返回 None。"""
    if not token:
        return None
    sess = _sessions.get(token)
    if sess is None:
        return None
    if time.time() - sess["created"] > _TTL:
        _sessions.pop(token, None)
        return None
    return sess


def consume_session(token: str) -> Session | None:
    """取出并删除会话（绑定完成后一次性消费）。"""
    sess = get_session(token)
    if sess is not None:
        _sessions.pop(token, None)
    return sess


def _cleanup() -> None:
    """清理所有已过期的会话。"""
    now = time.time()
    for token in [t for t, s in _sessions.items() if now - s["created"] > _TTL]:
        _sessions.pop(token, None)
