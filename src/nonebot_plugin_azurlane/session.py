"""一次性绑定会话：token -> {qq, cb}。

/绑定 指令生成短 token（10 分钟有效），登录 URL 只带 token，不暴露 QQ 与回调信息。
"""

import time
import secrets

# token -> {"qq": str, "cb": str, "created": float}
_sessions: dict[str, dict] = {}
_TTL = 10 * 60  # 10 分钟


def create_session(qq: str, cb: str) -> str:
    token = secrets.token_urlsafe(16)
    _sessions[token] = {"qq": qq, "cb": cb, "created": time.time()}
    _cleanup()
    return token


def get_session(token: str) -> dict | None:
    if not token:
        return None
    sess = _sessions.get(token)
    if sess is None:
        return None
    if time.time() - sess["created"] > _TTL:
        _sessions.pop(token, None)
        return None
    return sess


def consume_session(token: str) -> dict | None:
    """取出并删除会话（绑定完成后一次性消费）。"""
    sess = get_session(token)
    if sess is not None:
        _sessions.pop(token, None)
    return sess


def _cleanup() -> None:
    now = time.time()
    for token in [t for t, s in _sessions.items() if now - s["created"] > _TTL]:
        _sessions.pop(token, None)
