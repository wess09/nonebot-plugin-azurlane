"""HTML 面板渲染：用 nonebot-plugin-htmlrender 生成指挥官信息 / 建造记录图片。

面板内容不展示区服等敏感信息。
"""

import base64
from pathlib import Path

from nonebot_plugin_htmlrender import render_html

TEMPLATE_DIR = Path(__file__).parent / "templates"
# 项目根目录下的 data/blhx_logo.webp（碧蓝航线官方 logo，页眉用）
LOGO_PATH = Path(__file__).parent.parent.parent.parent / "data" / "blhx_logo.webp"
_MASCOT_PATHS = tuple(
    Path(__file__).parent.parent.parent.parent / "data" / "mascots" / name
    for name in ("ship_girl_1.png", "ship_girl_2.png", "ship_girl_3.png")
)
# 碧蓝航线游戏内字体（来自 data/ 目录）
_FONTS = {
    # 标题粗黑体
    "MStiffHei": Path(__file__).parent.parent.parent.parent / "data" / "MStiffHei.ttf",
    # 界面正文
    "SourceHanSans": Path(__file__).parent.parent.parent.parent / "data" / "SourceHanSans.ttf",
    # 艺术宋体标题
    "FZCYSK": Path(__file__).parent.parent.parent.parent / "data" / "FZCYSK.ttf",
    # 西文数字/英文标语
    "Agency": Path(__file__).parent.parent.parent.parent / "data" / "agency.ttf",
}


def _font_faces() -> str:
    """生成所有字体的 @font-face 内联样式（base64 内嵌）。"""
    faces = []
    for name, path in _FONTS.items():
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode()
            faces.append(
                f"@font-face{{font-family:'{name}';"
                f"src:url(data:font/truetype;base64,{b64}) format('truetype');}}"
            )
    return "".join(faces)


def _logo_data_uri() -> str:
    return _image_data_uri(LOGO_PATH, "image/webp")


def _image_data_uri(path: Path, media_type: str) -> str:
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{media_type};base64,{b64}"


def _fmt_collection_rate(v) -> str:
    """收集率：接口实际可能返回 "0.0%"（字符串）或 0~1 小数（文档），两种都兼容。"""
    if isinstance(v, str):
        return v if "%" in v else f"{v}%"
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"


def _rate_pct(v) -> float:
    """收集率数值（0~100），用于进度条宽度。"""
    if isinstance(v, str):
        try:
            return float(v.replace("%", ""))
        except ValueError:
            return 0.0
    try:
        return float(v) * 100
    except (TypeError, ValueError):
        return 0.0


def _fmt_number(v: int) -> str:
    return f"{v:,}"


async def _render(html: str) -> bytes:
    rendered = await render_html(
        html,
        width=540,
        device_pixel_ratio=2.0,
        timeout_seconds=30,
    )
    return rendered.data


def _fill(template_name: str, data: dict) -> str:
    html = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    # 注入字体的 @font-face（放于 <style> 标签内）
    html = html.replace(
        "<style>",
        "<style>" + _font_faces(),
    )
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", "" if value is None else str(value))
    return html


async def build_commanders_pic(detail: dict) -> bytes:
    ui = detail.get("user_info", {})
    stat = detail.get("statistics", {})
    pt = detail.get("progress_tracking", {})
    combat = detail.get("combat_overview", {})

    commissions = pt.get("commissions", {})
    research = pt.get("research", {})
    exercise = combat.get("exercise", {})
    ex_max = exercise.get("daily_max") or 10
    ex_remain = exercise.get("today_remaining") or 0
    ex_done = max(0, ex_max - ex_remain)

    challenges = [
        c
        for c in combat.get("daily_challenges", [])
        if (c.get("daily_challenge_remaining_attempts") or 0) > 0
    ]

    rate_str = _fmt_collection_rate(stat.get("collection_rate"))
    rate_pct = int(_rate_pct(stat.get("collection_rate")))
    rate_pct = int(_rate_pct(stat.get("collection_rate")))

    # 收集率圆环：SVG stroke-dasharray（半径 37）
    rate_circ = 2 * 3.1416 * 37
    rate_offset = rate_circ * (1 - rate_pct / 100)

    data = {
        "logo": _logo_data_uri(),
        "mascot_1": _image_data_uri(_MASCOT_PATHS[0], "image/png"),
        "mascot_2": _image_data_uri(_MASCOT_PATHS[1], "image/png"),
        "mascot_3": _image_data_uri(_MASCOT_PATHS[2], "image/png"),
        "avatar": ui.get("avatar") or "",
        "nickname": ui.get("nickname") or "",
        "level": ui.get("level") or "",
        "guild_name": ui.get("guild_name") or "未加入舰队",
        "collection_rate": rate_str,
        "rate_circ": f"{rate_circ:.2f}",
        "rate_offset": f"{rate_offset:.2f}",
        "mainline_progress": stat.get("mainline_progress") or "-",
        "coins": _fmt_number(stat.get("coins_current") or 0),
        "oil": _fmt_number(stat.get("oil_current") or 0),
        "food": _fmt_number(stat.get("food_current") or 0),
        "comm_in_progress": commissions.get("in_progress") or 0,
        "comm_completed": commissions.get("completed") or 0,
        "comm_idle": commissions.get("idle") or 0,
        "research_in_progress": research.get("in_progress") or 0,
        "research_completed": research.get("completed") or 0,
        "research_idle": research.get("idle") or 0,
        "exercise_remaining": ex_remain,
        "exercise_max": ex_max,
        "exercise_done": ex_done,
    }

    if challenges:
        challenge_rows = "".join(
            f"""
            <div class="todo-row">
              <span class="todo-name">{c.get('daily_challenge_name')}</span>
              <span class="todo-badge">剩 {c.get('daily_challenge_remaining_attempts')} 次</span>
            </div>
            """
            for c in challenges
        )
        data["challenges"] = challenge_rows
    else:
        data["challenges"] = (
            '<div class="todo-row"><span class="todo-done">今日副本已全部完成</span></div>'
        )

    return await _render(_fill("commander.html", data))


_RARITY_CLASS = {
    "超稀有": "ssr",
    "精锐": "sr",
    "稀有": "r",
    "普通": "n",
}


def _rarity_class(rarity: str) -> str:
    return _RARITY_CLASS.get(rarity, "r")


async def build_build_records_pic(result: dict) -> bytes:
    nickname = result.get("nickname") or ""
    records = result.get("records") or []
    total_count = result.get("total_count") or 0
    fetched = len(records)

    rows = ""
    for i, rec in enumerate(records, start=1):
        rarity = rec.get("rarity") or ""
        rows += f"""
        <div class="row">
          <span class="idx">{i}</span>
          <img class="ship-icon" src="{rec.get('avatarIcon') or ''}" alt="" />
          <span class="ship-name">{rec.get('roleName') or '-'}</span>
          <span class="task">{rec.get('taskName') or '-'}</span>
          <span class="rarity {_rarity_class(rarity)}">{rarity or '-'}</span>
        </div>
        """

    data = {
        "logo": _logo_data_uri(),
        "nickname": nickname,
        "avatar": result.get("avatar") or "",
        "fetched": fetched,
        "total_count": total_count,
        "rows": rows,
    }

    return await _render(_fill("build_record.html", data))
