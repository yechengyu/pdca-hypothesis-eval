#!/usr/bin/env python3
"""calibration_status.py — 校准信号够不够触发一次 rubric 优化。

规则（见 references/darwin_calibration.md）：自上次优化以来攒满 ≥5 条新校准信号
（尤其 recalibrate）就该做一次达尔文式优化 pass。周日复盘时跑一下即可。

用法：
  python3 calibration_status.py                 # 看够没够
  python3 calibration_status.py --mark-optimized # 做完优化后记基线，从这之后重新数
"""
import argparse
import json
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "references"
LOG = REF / "calibration_feedback.jsonl"
STATE = REF / "calibration_state.json"
THRESHOLD = 5


def load_entries():
    if not LOG.exists():
        return []
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_optimized_count": 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mark-optimized", action="store_true")
    args = ap.parse_args()

    entries = load_entries()
    total = len(entries)
    state = load_state()
    base = state.get("last_optimized_count", 0)

    if args.mark_optimized:
        STATE.write_text(json.dumps({"last_optimized_count": total}, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        print(f"✅ 已记基线：累计 {total} 条，下次从这之后重新数。")
        return

    new = total - base
    new_recal = sum(1 for e in entries[base:] if e.get("verdict") == "recalibrate")
    ready = new >= THRESHOLD
    print(f"校准信号：累计 {total} 条，自上次优化以来新增 {new} 条（其中 recalibrate {new_recal} 条）。")
    if ready:
        print(f"🟢 已达阈值（≥{THRESHOLD}）→ 建议做一次 rubric 优化 pass（见 darwin_calibration.md）。")
    else:
        print(f"⚪ 未达阈值（{new}/{THRESHOLD}）→ 继续攒，下个周日再看。")


if __name__ == "__main__":
    main()
