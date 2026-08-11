"""绑定数据存储：QQ 号 -> (uid, server_id, server_label)。

用 SQLite 持久化到 data/azurlane.db。敏感信息（区服、server_id）仅存于服务端，
不在任何查询回复/面板中展示。
"""

import os
import sqlite3
from dataclasses import dataclass

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
DB_PATH = os.path.join(DATA_DIR, "azurlane.db")


@dataclass
class Binding:
    uid: str
    server_id: str
    server_label: str  # 仅服务端内部使用，不展示给用户


_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        os.makedirs(DATA_DIR, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH)
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
    conn = _get_conn()
    row = conn.execute("SELECT uid, server_id, server_label FROM bindings WHERE qq=?", (qq,)).fetchone()
    if row is None:
        return None
    return Binding(uid=row["uid"], server_id=row["server_id"], server_label=row["server_label"])
