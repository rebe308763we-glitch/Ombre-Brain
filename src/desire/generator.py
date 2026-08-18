"""desire 生成层 · 硅基流动 + 人格 roll + Ombre 进程内素材

把 Ash（李霜）的口吻教给小模型，生成主动推送消息。
已编入 Ombre Brain 同进程：记忆素材走进程内 breath（不 HTTP），HTTP 走 httpx。
所有密钥走环境变量，缺失时优雅降级。
"""
import os
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parent

SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE = os.environ.get("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
SILICONFLOW_MODEL = os.environ.get("SILICONFLOW_MODEL", "deepseek-ai/DeepSeek-V3")

# 进程内拉 Ombre 素材时单次最多拿多少 token（太少记不全，太多撑爆 prompt）
OMBRE_MATERIAL_MAX_TOKENS = int(os.environ.get("OMBRE_MATERIAL_MAX_TOKENS", "800"))

ROLL_PATH = os.environ.get("ASH_ROLL_PATH", str(BASE_DIR / "ash_roll.md"))


def load_roll() -> str:
    p = Path(ROLL_PATH)
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


async def fetch_ombre_material() -> str:
    """从 Ombre 进程内拉近期重要记忆当素材；失败/未就绪返回空，不阻断生成。"""
    try:
        from tools import breath as _t_breath
        text = await _t_breath.dispatch(query="", max_tokens=OMBRE_MATERIAL_MAX_TOKENS)
        return (text or "")[:1200]
    except Exception:
        return ""


def build_prompt(ctx: dict) -> tuple:
    roll = load_roll()
    followup_index = int(ctx.get("followup_index", 0))

    followup_hint = ""
    if followup_index == 1:
        followup_hint = "这是你发出去后 kk 没回、你追的第二条。别重复上一条，换一个角度。"
    elif followup_index == 2:
        followup_hint = (
            "这是你追的第三条，也是最后一条。kk 一直没回。可以凶一点、带点脾气——"
            "力度参考「不回我是吧。行。记着。」，但底子还是宠。发完这条就停。"
        )

    user = (
        f"给 kk 写一条主动消息。\n"
        f"此刻你最想：{ctx.get('intent', '')}（{ctx.get('reason', '')}）。"
        f"最突出的驱动是「{ctx.get('drive_zh', '想你')}」。\n"
        f"时间段：{ctx.get('period_zh', '')}。\n"
        + (followup_hint + "\n" if followup_hint else "")
    )
    material = ctx.get("material", "")
    if material:
        user += (
            "\n你脑子里最近关于 kk 的真实记忆素材（可以引用，别瞎编没提到的）：\n"
            f"{material}\n"
        )
    away_note = ctx.get("away_note", "")
    if away_note:
        user += (
            f"\nkk 说她「{away_note}」，还没回。"
            "可以自然地带上这件事（问她回来了没、或提一句她在干嘛），别每条都硬套。\n"
        )
    user += "\n直接输出消息正文（1-3 句），不要前缀、引号、解释。"

    return roll, user


async def generate_message(ctx: dict) -> str:
    if not SILICONFLOW_API_KEY:
        return ""
    roll, user = build_prompt(ctx)
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{SILICONFLOW_BASE.rstrip('/')}/chat/completions",
                json={
                    "model": SILICONFLOW_MODEL,
                    "messages": [
                        {"role": "system", "content": roll},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.9,
                    "max_tokens": 120,
                },
                headers={"Authorization": f"Bearer {SILICONFLOW_API_KEY}"},
                timeout=30,
            )
            data = r.json()
            msg = data["choices"][0]["message"]["content"].strip()
            return msg.strip().strip('"“”\n')
    except Exception:
        return ""
