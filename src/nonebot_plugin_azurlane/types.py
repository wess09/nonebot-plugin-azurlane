"""共享类型定义：JSON 载荷与 le3-api 响应结构。"""

from typing import Any, TypedDict

# 任意 JSON 值 / 对象（接口返回的动态结构）
JsonValue = Any
JsonObj = dict[str, Any]


class UserInfo(TypedDict):
    nickname: str
    level: int
    server: str
    uid: str
    guild_name: str | None
    avatar: str


class Statistics(TypedDict):
    collection_rate: float | str
    mainline_progress: str
    coins_current: int
    oil_current: int
    food_current: int


class ProgressCounts(TypedDict):
    in_progress: int
    completed: int
    idle: int


class ProgressTracking(TypedDict):
    commissions: ProgressCounts
    research: ProgressCounts


class Exercise(TypedDict):
    daily_max: int | None
    today_remaining: int | None


class DailyChallenge(TypedDict):
    daily_challenge_name: str
    daily_challenge_remaining_attempts: int
    daily_total_attempts: int
    daily_challenge_id: int


class CombatOverview(TypedDict):
    exercise: Exercise
    daily_challenges: list[DailyChallenge]


class UserDetail(TypedDict):
    user_info: UserInfo
    statistics: Statistics
    progress_tracking: ProgressTracking
    combat_overview: CombatOverview


class BuildRecordItem(TypedDict):
    avatarIcon: str
    buildStartTime: int
    roleName: str
    taskName: str
    taskId: int
    rarity: str


class BuildRecordResult(TypedDict):
    nickname: str | None
    uid: str | None
    server_name: str | None
    avatar: str | None
    total_count: int
    records: list[BuildRecordItem]
