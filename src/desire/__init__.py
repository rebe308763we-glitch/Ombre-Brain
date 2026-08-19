"""desire 模块 · 编入 Ombre 的欲望引擎 + 主动推送子应用。

由 Ombre 的 server.py 在 DESIRE_ENABLED=true 时：
  1. `_app.mount("/desire", desire_app)` 挂子应用
  2. lifespan 里调 `start_notify_loop()` 启动推送循环
"""
from .server import desire_app, start_notify_loop, start_telegram_loop

__all__ = ["desire_app", "start_notify_loop", "start_telegram_loop"]
