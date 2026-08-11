"""共享类型定义：JSON 载荷与 le3-api 响应结构。"""

from typing import Any, TypedDict

# 任意 JSON 值 / 对象（接口返回的动态结构）
JsonValue = Any
JsonObj = dict[str, Any]


class UserInfo(TypedDict):
    """指挥官基础信息。"""

    nickname: str
    level: int
    server: str
    uid: str
    guild_name: str | None
    avatar: str


class Statistics(TypedDict):
    """指挥官统计信息。"""

    collection_rate: float | str
    mainline_progress: str
    coins_current: int
    oil_current: int
    food_current: int


class ProgressCounts(TypedDict):
    """进行中 / 已完成 / 空闲三项计数。"""

    in_progress: int
    completed: int
    idle: int


class ProgressTracking(TypedDict):
    """委托与科研的进度计数。"""

    commissions: ProgressCounts
    research: ProgressCounts


class Exercise(TypedDict):
    """演习信息（未开放时为 None）。"""

    daily_max: int | None
    today_remaining: int | None


class DailyChallenge(TypedDict):
    """每日挑战副本。"""

    daily_challenge_name: str
    daily_challenge_remaining_attempts: int
    daily_total_attempts: int
    daily_challenge_id: int


class CombatOverview(TypedDict):
    """战斗总览：演习与每日挑战。"""

    exercise: Exercise
    daily_challenges: list[DailyChallenge]


class UserDetail(TypedDict):
    """指挥官详情 get/user_detail 响应。"""

    user_info: UserInfo
    statistics: Statistics
    progress_tracking: ProgressTracking
    combat_overview: CombatOverview


class BuildRecordItem(TypedDict):
    """单条建造记录。"""

    avatarIcon: str
    buildStartTime: int
    roleName: str
    taskName: str
    taskId: int
    rarity: str


class BuildRecordResult(TypedDict):
    """建造记录分页拉取结果。"""

    nickname: str | None
    uid: str | None
    server_name: str | None
    avatar: str | None
    total_count: int
    records: list[BuildRecordItem]
