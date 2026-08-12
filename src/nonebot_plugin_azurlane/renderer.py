"""HTML 面板渲染：用 nonebot-plugin-htmlrender 生成指挥官信息 / 建造记录图片。

面板内容不展示区服等敏感信息。
"""

import base64
from pathlib import Path

from nonebot_plugin_htmlrender import render_html

from .types import UserDetail, BuildRecordResult

TEMPLATE_DIR = Path(__file__).parent / "templates"
# 包内 data/blhx_logo.webp（碧蓝航线官方 logo，页眉用）
LOGO_PATH = Path(__file__).parent / "data" / "blhx_logo.webp"
_MASCOT_PATHS = tuple(
    Path(__file__).parent / "data" / "mascots" / name
    for name in ("ship_girl_1.png", "ship_girl_2.png", "ship_girl_3.png")
)
_COLLECTION_MASCOT_PATHS = tuple(
    Path(__file__).parent / "data" / "mascots" / name
    for name in ("akashi_chibi.png", "laffey_chibi.png", "ayanami_chibi.png")
)
# 渲染用字体：TTF 装在系统里（C:\Windows\Fonts），@font-face 用 local() 直接引用，
# 不再 base64 内嵌，避免 27MB HTML 拖慢 playwright。
_SYSTEM_FACES = (
    # 正文思源黑体（先撞系统注册名，撞不中就 fallback）
    ("SourceHanSans", ["Source Han Sans CN", "Source Han Sans SC", "思源黑体"]),
    # 标题粗黑体
    ("MStiffHei", ["MStiffHei PRC", "MStiffHei"]),
    # 西文数字/英文标语
    ("Agency", ["Agency FB"]),
)

# 模板占位符数据：统一 str（占位符替换用）
TemplateData = dict[str, str]


def _font_faces() -> str:
    """生成所有字体的 @font-face（用 local() 引用系统字体，不 base64）。"""
    faces: list[str] = []
    for name, candidates in _SYSTEM_FACES:
        srcs = ", ".join(f"local('{c}')" for c in candidates)
        faces.append(f"@font-face{{font-family:'{name}';src:{srcs};}}")
    return "".join(faces)


def _logo_data_uri() -> str:
    """页眉 logo 的 data URI（文件缺失时为空串）。"""
    return _image_data_uri(LOGO_PATH, "image/webp")


def _image_data_uri(path: Path, media_type: str) -> str:
    """读取图片为 base64 data URI，文件缺失时返回空串。"""
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{media_type};base64,{b64}"


async def _network_image_data_uri(url: str) -> str:
    """把远程头像 URL 下载并转成 base64 data URI，供面板 <img> 内嵌。

    为什么不用 <img src="http://..."> 直接引用：
        头像 URL 来自 le3-api，可能为空、或网络不可达。若交给 playwright/Edge 在
        渲染时联网拉取，拉不到就会坏图，还会拖住 networkidle 让整张面板渲染卡顿。
        改成由 bot（已有 httpx）先下载好、内嵌成 data URI，渲染过程完全不碰外网。

    参数：
        url — le3-api 返回的头像地址（可能为空字符串或非法值）。

    返回：
        成功 → 形如 "data:image/webp;base64,...." 的 data URI；
        失败（URL 为空/非法/下载异常）→ 回退本地 data/logo.webp 的 data URI，
        保证 <img> 不会因为空 src 渲染出破损图片。
    """
    # 1) 只有 http(s) 链接才尝试下载；否则直接走回退。
    url = url.strip()
    if url.startswith(("http://", "https://")):
        try:
            import httpx

            # trust_env=False：绕过系统代理直连，避免代理劫持 TLS（与 le3api 一致）。
            async with httpx.AsyncClient(timeout=httpx.Timeout(8), trust_env=False) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            b64 = base64.b64encode(resp.content).decode()
            media_type = resp.headers.get("Content-Type", "image/*").split(";")[0] or "image/*"
            return f"data:{media_type};base64,{b64}"
        except Exception:
            # 下载失败（网络不可达 / 404 / 超时）落到下方回退。
            pass

    # 2) 回退路径：URL 缺失或不可达时，用本地 logo.webp 兜底，避免坏图。
    return _image_data_uri(Path(__file__).parent / "data" / "logo.webp", "image/webp")


def _fmt_collection_rate(v: object) -> str:
    """收集率：接口实际可能返回 "0.0%"（字符串）或 0~1 小数（文档），两种都兼容。"""
    if isinstance(v, str):
        return v if "%" in v else f"{v}%"
    if isinstance(v, (int, float)):
        return f"{float(v) * 100:.1f}%"
    return "-"


def _rate_pct(v: object) -> float:
    """收集率数值（0~100），用于进度条宽度。"""
    if isinstance(v, str):
        try:
            return float(v.replace("%", ""))
        except ValueError:
            return 0.0
    if isinstance(v, (int, float)):
        return float(v) * 100
    return 0.0


def _fmt_number(v: int) -> str:
    """格式化数字为带千分位的字符串（如 1,234,567）。"""
    return f"{v:,}"


async def _render(html: str) -> bytes:
    """调用 htmlrender 将 HTML 渲染为 PNG bytes。"""
    rendered = await render_html(
        html,
        width=540,
        device_pixel_ratio=2.0,
        timeout_seconds=120,
    )
    return rendered.data


def _fill(template_name: str, data: TemplateData) -> str:
    """读取模板并注入 @font-face 与 {{KEY}} 占位符，返回完整 HTML。"""
    html = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    # 注入字体的 @font-face（放于 <style> 标签内）。
    html = html.replace(
        "<style>",
        "<style>" + _font_faces(),
    )
    for key, value in data.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def _as_str(v: object) -> str:
    """对象转字符串，None 归一为空串。"""
    return "" if v is None else str(v)


async def build_commanders_pic(detail: UserDetail) -> bytes:
    """构建指挥官信息面板图片。"""
    ui = detail["user_info"]
    stat = detail["statistics"]
    pt = detail["progress_tracking"]
    combat = detail["combat_overview"]

    commissions = pt["commissions"]
    research = pt["research"]
    exercise = combat["exercise"]
    ex_max = exercise["daily_max"] or 10
    ex_remain = exercise["today_remaining"] or 0
    ex_done = max(0, ex_max - ex_remain)

    challenges = [
        c for c in combat["daily_challenges"] if c["daily_challenge_remaining_attempts"] > 0
    ]

    rate_str = _fmt_collection_rate(stat["collection_rate"])
    rate_pct = int(_rate_pct(stat["collection_rate"]))

    # 收集率圆环：SVG stroke-dasharray（半径 37）。
    rate_circ = 2 * 3.1416 * 37
    rate_offset = rate_circ * (1 - rate_pct / 100)

    data: TemplateData = {
        "logo": _logo_data_uri(),
        "mascot_1": _image_data_uri(_MASCOT_PATHS[0], "image/png"),
        "mascot_2": _image_data_uri(_MASCOT_PATHS[1], "image/png"),
        "mascot_3": _image_data_uri(_MASCOT_PATHS[2], "image/png"),
        "collection_mascot_1": _image_data_uri(_COLLECTION_MASCOT_PATHS[0], "image/png"),
        "collection_mascot_2": _image_data_uri(_COLLECTION_MASCOT_PATHS[1], "image/png"),
        "collection_mascot_3": _image_data_uri(_COLLECTION_MASCOT_PATHS[2], "image/png"),
        "avatar": await _network_image_data_uri(_as_str(ui["avatar"])),
        "nickname": _as_str(ui["nickname"]),
        "level": _as_str(ui["level"]),
        "guild_name": _as_str(ui["guild_name"] or "未加入舰队"),
        "collection_rate": rate_str,
        "rate_circ": f"{rate_circ:.2f}",
        "rate_offset": f"{rate_offset:.2f}",
        "mainline_progress": _as_str(stat["mainline_progress"] or "-"),
        "coins": _fmt_number(stat["coins_current"]),
        "oil": _fmt_number(stat["oil_current"]),
        "food": _fmt_number(stat["food_current"]),
        "comm_in_progress": _as_str(commissions["in_progress"]),
        "comm_completed": _as_str(commissions["completed"]),
        "comm_idle": _as_str(commissions["idle"]),
        "research_in_progress": _as_str(research["in_progress"]),
        "research_completed": _as_str(research["completed"]),
        "research_idle": _as_str(research["idle"]),
        "exercise_remaining": _as_str(ex_remain),
        "exercise_max": _as_str(ex_max),
        "exercise_done": _as_str(ex_done),
    }

    if challenges:
        challenge_rows = "".join(
            f"""
            <div class="todo-row">
              <span class="todo-name">{c["daily_challenge_name"]}</span>
              <span class="todo-badge">剩 {c["daily_challenge_remaining_attempts"]} 次</span>
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


_RARITY_CLASS: dict[str, str] = {
    "超稀有": "ssr",
    "精锐": "sr",
    "稀有": "r",
    "普通": "n",
}


def _rarity_class(rarity: str) -> str:
    return _RARITY_CLASS.get(rarity, "r")


async def build_build_records_pic(result: BuildRecordResult) -> bytes:
    """构建建造记录面板图片。"""
    nickname = result["nickname"] or ""
    records = result["records"]
    total_count = result["total_count"]
    fetched = len(records)

    rows = ""
    for i, rec in enumerate(records, start=1):
        rarity = rec["rarity"]
        rows += f"""
        <div class="row">
          <span class="idx">{i}</span>
          <img class="ship-icon" src="{rec["avatarIcon"]}" alt="" />
          <span class="ship-name">{rec["roleName"] or "-"}</span>
          <span class="task">{rec["taskName"] or "-"}</span>
          <span class="rarity {_rarity_class(rarity)}">{rarity or "-"}</span>
        </div>
        """

    data: TemplateData = {
        "logo": _logo_data_uri(),
        "nickname": nickname,
        "avatar": await _network_image_data_uri(_as_str(result["avatar"])),
        "fetched": _as_str(fetched),
        "total_count": _as_str(total_count),
        "rows": rows,
    }

    return await _render(_fill("build_record.html", data))
