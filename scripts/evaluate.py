#!/usr/bin/env python3
"""evaluate.py — PDCA 假设多模型交叉验证（可选增强，非核心依赖）。

核心 skill 由运行它的宿主 AI 直接按 rubric 打分，**不需要本脚本、不需要任何 key**。
本脚本仅供"想用外部大模型交叉验证、且自己配了 key"的场景：对一条假设，让每个已配
key 的外部模型按同一 rubric 打分（每维 0-2 + 依据），输出结构化 JSON，便于看分歧。

模型 key 从环境变量读（也支持 skill 目录下的 .env，便于分发后本地配置）：
  ARK_API_KEY        豆包/火山方舟
  DEEPSEEK_API_KEY   DeepSeek
缺 key 的模型自动跳过并标注，不报错。

用法：
  python3 evaluate.py --hypothesis-file hyp.txt --rubric rubric/pdca_rubric.json
  python3 evaluate.py --hypothesis "做X预期Y，检验标准≥..." --rubric ...
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# 模型注册表：name -> (endpoint, model_id, api_key_env)
MODELS = {
    "豆包": (
        "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        os.environ.get("ARK_TEXT_MODEL", "doubao-seed-1-6-250615"),
        "ARK_API_KEY",
    ),
    "DeepSeek": (
        "https://api.deepseek.com/chat/completions",
        os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        "DEEPSEEK_API_KEY",
    ),
}


def load_dotenv():
    """把 skill 目录下 .env（若有）灌进 os.environ，不覆盖已有值。分发后本地配 key 用。"""
    for p in (SKILL_DIR / ".env", Path.home() / ".config" / "yotime-market-ops" / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def build_prompt(rubric, hypothesis):
    dims = rubric["dimensions"]
    lines = [
        "你是 PDCA 假设评估器。只评估『假设作为一个可被数据验证的命题』的方法论质量，",
        "不替写业务内容、不评判业务方向对不对。严格按下面 rubric 逐维度打分。",
        "",
        "# Rubric（每维 0-2 分）",
    ]
    for d in dims:
        lines.append(f"## {d['id']} · {d['name']}（权重 {d['weight']}）")
        lines.append(f"问：{d['ask']}")
        for s in ("0", "1", "2"):
            lines.append(f"  {s} 分 = {d['scoring'][s]}")
    lines += [
        "",
        "# 待评估假设",
        hypothesis,
        "",
        "# 输出（严格 JSON，不要多余文字）",
        '{"dimensions": {"<id>": {"score": 0-2, "why": "一句依据"}, ...}}',
        "每个维度 id 都要出现。why 必须具体引用假设里的内容，不要泛泛而谈。",
    ]
    return "\n".join(lines)


def call_model(endpoint, model_id, api_key, prompt, timeout=120):
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def parse_json(text):
    """从模型回复里抠出 JSON（容忍 ```json 包裹和前后噪声）。"""
    t = text.strip()
    if "```" in t:
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j < 0:
        raise ValueError(f"无 JSON: {text[:200]}")
    return json.loads(t[i:j + 1])


def score_one(rubric, parsed):
    """把模型给的逐维 score 折算成加权总分 + 评级。"""
    dims = {d["id"]: d for d in rubric["dimensions"]}
    got = parsed.get("dimensions", {})
    total = max_total = 0
    norm = {}
    for did, d in dims.items():
        w = d.get("weight", 1)
        s = got.get(did, {})
        sc = int(s.get("score", 0)) if str(s.get("score", "")).strip() != "" else 0
        sc = max(0, min(2, sc))
        total += sc * w
        max_total += 2 * w
        norm[did] = {"score": sc, "why": s.get("why", "")}
    pct = total / max_total if max_total else 0
    band = next((b["band"] for b in rubric["verdict_bands"] if pct >= b["min_pct"]), "?")
    return {"dimensions": norm, "total": total, "max": max_total, "pct": round(pct, 3), "band": band}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hypothesis")
    ap.add_argument("--hypothesis-file")
    ap.add_argument("--rubric", default=str(SKILL_DIR / "rubric" / "pdca_rubric.json"))
    args = ap.parse_args()

    load_dotenv()

    if args.hypothesis_file:
        hypothesis = Path(args.hypothesis_file).read_text(encoding="utf-8").strip()
    elif args.hypothesis:
        hypothesis = args.hypothesis
    else:
        hypothesis = sys.stdin.read().strip()
    if not hypothesis:
        print(json.dumps({"error": "空假设"}, ensure_ascii=False))
        return 1

    rubric = json.loads(Path(args.rubric).read_text(encoding="utf-8"))
    prompt = build_prompt(rubric, hypothesis)

    out = {"rubric_version": rubric.get("version"), "models": {}}
    for name, (endpoint, model_id, key_env) in MODELS.items():
        api_key = os.environ.get(key_env)
        if not api_key:
            out["models"][name] = {"available": False, "error": f"{key_env} 未配置"}
            continue
        try:
            raw = call_model(endpoint, model_id, api_key, prompt)
            parsed = parse_json(raw)
            res = score_one(rubric, parsed)
            res["available"] = True
            res["model_id"] = model_id
            out["models"][name] = res
        except urllib.error.HTTPError as e:
            out["models"][name] = {"available": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8','ignore')[:200]}"}
        except Exception as e:
            out["models"][name] = {"available": False, "error": str(e)}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
