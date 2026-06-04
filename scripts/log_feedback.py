#!/usr/bin/env python3
"""log_feedback.py — 记录人工对一次 AI 评估的校准反馈。

每次 skill 评完一条假设，金标准评审者补一句「评得对 / 需校准+怎么改」，
本脚本把它连同 AI 当时的打分追加到 references/calibration_feedback.jsonl。
这些反馈是后续优化 rubric 的训练信号（向人的判断校准）。

用法：
  python3 log_feedback.py \
    --hypothesis "假设原文(可截断)" \
    --ai-band "B 基本成立" --ai-total 19 --ai-max 24 \
    --verdict ok            # 或 recalibrate
    --comment "检验时点这维度你给宽松了，应该是0不是1"
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "references" / "calibration_feedback.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypothesis", required=True)
    ap.add_argument("--ai-band", default="")
    ap.add_argument("--ai-total", type=int, default=0)
    ap.add_argument("--ai-max", type=int, default=0)
    ap.add_argument("--rubric-version", default="")
    ap.add_argument("--verdict", choices=["ok", "recalibrate"], required=True,
                    help="ok=AI评得对（正样本）/ recalibrate=需校准（含修正意见）")
    ap.add_argument("--comment", default="", help="需校准时写清哪个维度/分数该怎么改")
    ap.add_argument("--reviewer", default="reviewer")
    ap.add_argument("--date", default="", help="ISO 日期；留空则用脚本运行时间")
    args = ap.parse_args()

    entry = {
        "ts": args.date or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "reviewer": args.reviewer,
        "hypothesis": args.hypothesis,
        "ai": {"band": args.ai_band, "total": args.ai_total, "max": args.ai_max,
               "rubric_version": args.rubric_version},
        "verdict": args.verdict,
        "comment": args.comment,
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    n = sum(1 for _ in LOG.open(encoding="utf-8"))
    print(f"✅ 已记入校准库（第 {n} 条）：{args.verdict}　{args.comment[:40]}")


if __name__ == "__main__":
    main()
