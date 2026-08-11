"""绑定数据存储：QQ 号 -> (uid, server_id, server_label)。

用 SQLite 持久化，数据目录由 nonebot-plugin-localstore 管理。
敏感信息（区服、server_id）仅存于服务端，不在任何查询回复/面板中展示。
"""

import sqlite3
from dataclasses import dataclass

from nonebot import require

require("nonebot_plugin_localstore")

from nonebot_plugin_localstore import get_plugin_data_dir


@dataclass
class Binding:
    """一条 QQ 绑定记录。"""

    uid: str
    server_id: str
    server_label: str  # 仅服务端内部使用，不展示给用户。


_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    """惰性初始化 SQLite 连接，首次调用时建表。"""
    global _conn
    if _conn is None:
        data_dir = get_plugin_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(data_dir / "azurlane.db"))
        _conn.row_factory = sqlite3.Row
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bindings (
                qq          TEXT PRIMARY KEY,
                uid         TEXT NOT NULL,
                server_id   TEXT NOT NULL,
                server_label TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _conn.commit()
    return _conn


def save_binding(qq: str, binding: Binding) -> None:
    """写入绑定记录，已存在则按 QQ 覆盖更新。"""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO bindings (qq, uid, server_id, server_label) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(qq) DO UPDATE SET "
        "uid=excluded.uid, server_id=excluded.server_id, server_label=excluded.server_label",
        (qq, binding.uid, binding.server_id, binding.server_label),
    )
    conn.commit()


def get_binding(qq: str) -> Binding | None:
    """按 QQ 查询绑定记录，未绑定返回 None。"""
    conn = _get_conn()
    sql = "SELECT uid, server_id, server_label FROM bindings WHERE qq=?"
    row = conn.execute(sql, (qq,)).fetchone()
    if row is None:
        return None
    return Binding(uid=row["uid"], server_id=row["server_id"], server_label=row["server_label"])
