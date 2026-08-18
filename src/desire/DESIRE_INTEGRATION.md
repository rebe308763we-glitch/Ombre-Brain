# DESIRE_INTEGRATION.md — desire 编入 Ombre 的集成说明

desire（欲望引擎 + 主动推送）已作为独立模块编入 Ombre Brain，进程内共享记忆。
代码全部在 `src/desire/`，不改 Ombre 现有业务逻辑。

## 开关

- `DESIRE_ENABLED=true`：挂载 `/desire` 子应用 + 启动推送循环。
- 默认 false：desire 完全不起作用，Ombre 不受任何影响。出问题随时设回 false 即可关掉。

## 集成点（更新 Ombre / merge 上游时，只检查这 2 处）

1. **breath 进程内调用** — `src/desire/generator.py` 的 `fetch_ombre_material()`
   里 `from tools import breath as _t_breath` + `await _t_breath.dispatch(query="", max_tokens=...)`。
   若上游改了 breath 的 dispatch 签名/位置，这里跟着改。

2. **挂载 + 循环启动** — `src/server.py` 的 `__main__` 块里，`_app = build_http_app(...)` 之后：
   `_app.mount("/desire", ...)` + 用 `asynccontextmanager` 包一层 lifespan 调 `start_notify_loop()`。
   若上游改了 `build_http_app` / lifespan 装配，检查这一段。

## 配置（环境变量）

- `DESIRE_ENABLED`：开关（默认 false）
- `DESIRE_DATA_DIR`：引擎状态落盘目录，默认 `/app/buckets/desire`（持久卷）
- `SILICONFLOW_API_KEY` / `SILICONFLOW_BASE_URL` / `SILICONFLOW_MODEL`：生成层
- `ASH_ROLL_PATH`：人格 roll，默认 `src/desire/ash_roll.md`
- `TG_BOT_TOKEN` / `TG_CHAT_ID`：Telegram 推送 + pinned message 备份
- `NTFY_TOPIC` / `NTFY_URL`：ntfy 推送
- `NOTIFY_INTERVAL_SECONDS`：推送循环间隔，默认 900（15min）
- `NOTIFY_COOLDOWN_SECONDS` / `FOLLOWUP_COOLDOWN_SECONDS` / `DAILY_NOTIFY_CAP`：冷却/上限

## 端点（DESIRE_ENABLED=true 后挂载在 /desire 下）

- `/desire/mcp` — desire 的 MCP（desire_state / desire_event / desire_feed），Ash 连这里
- `/desire/api/state`、`/desire/heartbeat`、`/desire/api/test_notify`、`/desire/api/test_generate`

## 回滚

- `DESIRE_ENABLED=false` 即可彻底关掉 desire，Ombre 原样运行。
- 代码级回滚：整体删除 `src/desire/` + 还原 `src/server.py` 的 desire 集成段。
