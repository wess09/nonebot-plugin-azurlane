# 碧蓝航线小程序 API 文档

> 本文档整理自插件 `main.py` 的实际调用，用于记录 B 站碧蓝航线微信小程序后端的接口约定。
> 这些接口**没有公开文档**，属逆向 + 模拟调用，字段和地址可能随小程序版本变化。若接口失效，需抓包重新确认。

## 0. 接口范围（已枚举确认）

> **确认方式**：对 `le3-api` 全路径前缀（`get/`、`post/`、`list/`、`query/`、`info/`）与动作名做 HTTP 枚举。**判据：有效接口返回 `HTTP 200`（无参数时 `code:-400` 缺参提示），无效路径返回 `HTTP 404`。**

`le3-api` 上可用的查询接口**只有 2 个**，其余路径全部 `404`：

- `get/user_detail` — 指挥官详情
- `get/build_record` — 建造记录

如需舰船图鉴、装备等**静态数据**，不走 `le3-api`，改用公开 Wiki（实测 blyy 项目使用）：
- `wiki.biligame.com/blhx`（B 站游戏 Wiki）
- `www.gamekee.com`（GameKee 攻略站）

### 服务器可用性（实测确认）

| 服务器类型 | server_id | 实测结果 |
| --- | --- | --- |
| 官网服 | `100 + 序号`（如官网11服 `111`） | `code:0` Success，真实玩家数据完整返回 |
| iOS 服 | `200 + 序号`（如 iOS1服 `201`） | `code:0` Success，接口认识该 ID |
| 渠道服 | `300 + 序号`（如 `301`） | `code:-1`「前方拥堵」，**接口不认识渠道服 ID，渠道服无法查询** |

> 渠道服（华为/小米/应用宝等）玩家账号体系独立于 B 站，`le3-api` 无渠道服数据。若按数字透传输入渠道服 ID，接口返回 `code:-1`，会显示「前方拥堵」而非正常数据。

## 1. 接口概况

| 项 | 值 |
| --- | --- |
| Base URL | `https://le3-api.game.bilibili.com/x/api/azurlane` |
| 传输协议 | HTTPS，`GET` |
| 数据格式 | JSON |
| 游戏标识 | `game_id = "182"`（所有请求携带） |

### 1.1 统一响应结构

所有接口返回同样的信封结构：

```json
{
  "code": 0,
  "message": "",
  "data": { }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | int | `0` 表示成功；非 `0` 表示接口错误 |
| `message` | string | 错误时的提示文案（如 Cookie 失效） |
| `data` | object | 业务数据，仅在 `code == 0` 时有意义 |

**错误处理约定**：调用方先判断 `data.get("code") != 0`，非 0 直接中止并返回 `message`，不再解析 `data`。

### 1.2 公共请求头

所有请求必须携带以下请求头，用于**伪装成微信小程序客户端**（缺少会被接口拒绝）：

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781
Referer: https://servicewechat.com/wx3ee6dc49667f3444/26/page-frame.html
Content-Type: application/json
```

- `User-Agent` 末尾的 `MicroMessenger/7.0.20.1781` 是微信内置浏览器标识，用于通过「仅小程序可访问」校验。
- `Referer` 指向小程序源码页面，同为来源校验。
- **Cookie（可选）**：请求时注入插件配置中的 `cookie`，可为空。部分接口（如建造记录）不带 Cookie 可能拿不到数据。

### 1.3 服务器 ID

`server_id` 参数为字符串形式的数字 ID，如官网 20 服 `"120"`、iOS 1 服 `"201"`。中文名到 ID 的映射见插件内 `server_map`，支持模糊匹配与数字透传（未收录的新服 ID 也能直接用）。

---

## 2. 指挥官详情

获取玩家的等级、资源、收集率、待办副本等概览数据。

### 2.1 请求

```
GET https://le3-api.game.bilibili.com/x/api/azurlane/get/user_detail
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `role_id` | string | ✅ | 游戏内 UID |
| `server_id` | string | ✅ | 服务器数字 ID |
| `game_id` | string | ✅ | 固定 `"182"` |

### 2.2 响应（`data` 字段结构）

```json
{
  "user_info": {
    "nickname": "指挥官昵称",
    "level": 120,
    "server": "官网20服-秋季旅行",
    "uid": "13xxxx",
    "guild_name": "舰队名",
    "avatar": "https://i0.hdslb.com/bfs/game/tmp/azurlane/206038.png"
  },
  "statistics": {
    "collection_rate": 0.72,
    "mainline_progress": "13-4",
    "coins_current": 123456,
    "oil_current": 4567,
    "food_current": 890
  },
  "progress_tracking": {
    "commissions": { "in_progress": 2, "completed": 1, "idle": 1 },
    "research":     { "in_progress": 1, "completed": 0, "idle": 2 }
  },
  "combat_overview": {
    "exercise": { "today_remaining": 10 },
    "daily_challenges": [
      { "daily_challenge_name": "关卡名", "daily_challenge_remaining_attempts": 1 }
    ]
  }
}
```

| 块 | 字段 | 类型 | 说明 |
| --- | --- | --- | --- |
| `user_info` | `nickname` | string | 指挥官昵称 |
| | `level` | int | 指挥官等级 |
| | `server` | string | 服务器显示全名 |
| | `uid` | string | 游戏内 UID |
| | `guild_name` | string\|null | 舰队名，无舰队为 null |
| | `avatar` | string | 指挥官头像 URL（B 站 CDN PNG） |
| `statistics` | `collection_rate` | number | 舰船收集率（0~1 小数；实测可能返回 `"61.6%"` 字符串） |
| | `mainline_progress` | string | 主线进度，如 `"13-4"` |
| | `coins_current` | int | 当前物资 |
| | `oil_current` | int | 当前石油 |
| | `food_current` | int | 当前存粮（食物） |
| `progress_tracking` | `commissions` | object | 委托状态，含 `in_progress` / `completed` / `idle` |
| | `research` | object | 科研状态，含 `in_progress` / `completed` / `idle` |
| `combat_overview` | `exercise.today_remaining` | int | 今日剩余演习次数（总 10 次） |
| | `daily_challenges[]` | array | 今日每日挑战列表 |
| | `daily_challenge_name` | string | 挑战关卡名 |
| | `daily_challenge_remaining_attempts` | int | 剩余挑战次数，`> 0` 表示还有待办 |

> **插件使用**：`daily_challenges` 中 `remaining_attempts > 0` 的项即「待办副本」；若全部为 0，回复「今日副本已全部完成」。

---

## 3. 建造记录

获取玩家的建造记录，接口分页返回，单页上限 50 条。

### 3.1 请求

```
GET https://le3-api.game.bilibili.com/x/api/azurlane/get/build_record
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `role_id` | string | ✅ | 游戏内 UID |
| `server_id` | string | ✅ | 服务器数字 ID |
| `page_num` | string | ✅ | 页码，从 `1` 开始 |
| `page_size` | string | ✅ | 单页条数，最大 `50` |

### 3.2 分页约定

- 插件按每页 50 条循环拉取，直到凑够目标数量（默认 10，上限 500）。
- 目标数量不是 50 的整数倍时，**最后一页的 `page_size` 取剩余量**（如目标 30 → 第 1 页 30 条）。
- 任一次分页返回 `code != 0` 或空数据即中断。

### 3.3 响应（`data` 字段结构）

```json
{
  "nickname": "指挥官昵称",
  "uid": "13xxxx",
  "serverName": "官网20服-秋季旅行",
  "avatar": "https://i0.hdslb.com/bfs/game/tmp/azurlane/xxxx.png",
  "buildRecords": {
    "total_count": 500,
    "data": [
      {
        "avatarIcon": "https://i0.hdslb.com/bfs/game/tmp/azurlane/401190.png",
        "buildStartTime": 1786422649,
        "roleName": "赫尔米娜",
        "taskName": "轻型建造",
        "taskId": 2,
        "rarity": "稀有"
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `nickname` | string | 指挥官昵称 |
| `uid` | string | 游戏内 UID |
| `serverName` | string | 服务器显示全名 |
| `avatar` | string | 指挥官头像 URL |
| `buildRecords.total_count` | int | 服务器上该玩家**实际总记录数**（可能大于本次拉取量） |
| `buildRecords.data[]` | array | 单页建造记录 |
| `avatarIcon` | string | **舰娘头像 URL**（B 站 CDN PNG） |
| `buildStartTime` | int | 建造开始时间戳（Unix 秒） |
| `roleName` | string | 建造出的舰船名 |
| `taskName` | string | 建造池名称（如轻型建造、特型建造等） |
| `taskId` | int | 建造池 ID（如轻型建造为 `2`） |
| `rarity` | string | 稀有度（如 `"稀有"`、`"超稀有"` 等） |

> `total_count` 与 `len(all_records)` 的关系：`total_count` 是接口侧的真实总数，`all_records` 是插件按目标数量拉取到的条数，两者可能不同。插件表头同时显示这两个值。

---

## 4. 服务器列表与状态（AzurLaneServerStatus）

> **权威来源**：本服务的上游是你的 **`AzurLaneServerStatus`** 项目（`server-checker.nanoda.work`），它**直接连接各服真实游戏网关**（官网/日/美/韩/台走 TCP protobuf 协议，iOS/渠道走 HTTP JSON），返回**实时状态**而非静态名单。7 个地区共 81 个服务器。

```
GET https://server-checker.nanoda.work/api/v1/status
```

**端点**：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/status` | 全部/指定地区服务器明细 |
| GET | `/api/v1/summary` | 各状态计数汇总 |
| GET | `/api/v1/regions` | 支持的地区列表 |
| GET | `/api/v1/regions/{key}` | 单地区明细 |
| GET | `/api/v1/servers/{region}_{id}` | 单服务器（如 `cn_28`、`cn_ios_1`） |
| GET | `/healthz` | 存活探针 |

**地区 key**：`cn`、`cn_ios`、`cn_channel`、`jp`、`en`、`kr`、`tw`

**`/api/v1/status` 响应结构**：

```json
{
  "generated_at": "2026-08-11T05:59:22Z",
  "regions": [
    {
      "key": "cn",
      "name": "CN Bilibili",
      "error": null,
      "cached": true,
      "queried_at": "...",
      "total": 30,
      "servers": [
        { "id": 20, "name": "秋季旅行", "status": "normal", "tag": null }
      ]
    }
  ]
}
```

| 字段 | 说明 |
| --- | --- |
| `generated_at` | 列表生成时间（实时更新） |
| `regions[].key` / `name` | 地区 key（`cn`/`cn_ios`/...）与显示名 |
| `regions[].error` | 查询错误（`timeout`/`refused`/`network_error`/`parse_error`），正常为 null |
| `regions[].cached` | 本次是否命中缓存 |
| `servers[].id` | **游戏网关协议原生的纯序号**（官网 1~30、iOS 1~11、渠道 1~6） |
| `servers[].name` | 服务器中文名 |
| `servers[].status` | 状态：`normal` / `maintenance` / `full` / `reg_full` / `unopened` / `unknown` |
| `servers[].tag` | 运营标记：`new` 新服 / `hot` 热门 / null |

**状态 → 协议映射**（`checker.py` `_STATUS_MAP`）：`0`→normal、`1`→maintenance、`2`→full、`3`→reg_full、`99`→unopened、其他→unknown。`tag`：`1`→hot、`2`→new。

### 与本服务（B 站 le3-api）的 ID 换算

`AzurLaneServerStatus` 返回的 `id` 是**游戏协议原生纯序号**。而 B 站小程序后端 `le3-api` 的 `server_id` 带 B 站自加的前缀，**只有对接 le3-api 时才需要换算**：

| 地区 | le3-api server_id | 示例 |
| --- | --- | --- |
| `cn`（官网） | `100 + id` | 秋季旅行 id=20 → `120` |
| `cn_ios` | `200 + id` | 马耳他 id=11 → `211` |
| `cn_channel`（渠道） | **不适用** | 渠道服 le3-api 无数据（实测 `code:-1`） |

**缓存与限流**（`AzurLaneServerStatus` 自带）：新鲜窗口 8 秒、单 IP 并发 >10 返回 `429`、客户端无法绕过缓存（无 `refresh` 参数）。接入方应**优先利用其缓存**，避免频繁拉取。

---

## 5. 使用注意与局限

1. **无官方文档**：字段、地址、校验均为逆向结果，小程序更新可能导致失效，失效需重新抓包。
2. **依赖 Cookie**：部分接口要求配置 `cookie`，失效时 `code != 0` 并返回 message。
3. **模拟调用风险**：接口为个人小程序后端，频繁调用可能触发风控/封禁，勿用于商业用途。
4. **防刷屏**：建造记录超过 20 条时插件改用合并转发消息发送，这是客户端行为，非接口要求。
