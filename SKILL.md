---
name: pdca-hypothesis-eval
description: >-
  Evaluate the methodological quality of a PDCA hypothesis (假设) and score it
  against a rubric, then give methodology-level coaching to improve it.
  Use this whenever the user wants to score, grade, evaluate, sanity-check, or
  improve a hypothesis / 假设 / experiment design — e.g. "评估这条假设"、"我这个
  假设打几分"、"这个假设成立吗"、"帮我看看检验标准设计得好不好"、"PDCA 打分"、
  "score my hypothesis"、"is this a testable hypothesis". The user pastes the
  hypothesis content directly (assumption / 检验标准 / 检验时点, or free text);
  this skill needs no database, no network, and no API keys — the AI running it
  scores against the bundled rubric directly. Trigger even when the user only
  says "看看我这个想法能不能验证" or describes a test they want to run without
  using the word "假设".
---

# PDCA 假设教练

**这是个教练，不是裁判。** 目的是帮使用者**长出"会写可验证假设"的能力**——
每评一条，都要让他清楚地知道：哪里弱、为什么弱、照着怎么改、下次怎么自己避开。

分数只是诊断手段、是佐证；**主菜是教练式改进建议**。一次评估如果只给了个分、
没让使用者学到"下次怎么写得更好"，就是失败的。

只教**方法论**（怎么把想法写成能被数据证伪的命题），**不替写业务内容、不评判业务方向对不对**——
做 X 还是做 Y 是人的判断；这里只帮他把"要验证的命题"立扎实。

## 何时用

用户给一条假设/想法要打分、评估、找毛病、或问"这个假设成立吗 / 能不能验证"。
用户**直接把内容贴进来**（结构化或自然语言都行），不需要连任何数据库、不需要任何 key。

## 评估标尺（rubric）

唯一标尺是 `rubric/pdca_rubric.json`——**先读它**。它定义若干维度、各自权重和 0-2 分打分细则、
以及总分对应的 A/B/C/D 评级。这个文件是可进化的（见 `references/darwin_calibration.md`：
会根据资深评审者的人工反馈持续校准），所以**永远以文件当前内容为准，别把维度背死**。

## 工作流程

### 1. 解析假设
从用户输入里抽出四要素（有就抽，没有就标记缺失）：
- **假设**（做什么 → 预期什么）
- **检验标准**（怎么算成功，量化阈值）
- **检验时点**（哪天看结果）
- **干扰因素 / 数据源**（可选但加分项）

自然语言输入也照抽，抽不到的要件就当"缺失"，这本身是评估结果的一部分。

### 2. 按 rubric 打分（你自己来，不需要外部模型）
**先读 `rubric/pdca_rubric.json`**，对照每个维度的 0-2 打分细则，逐维度给分 + 一句依据，
按权重算总分和 A/B/C/D 评级。你（运行本 skill 的 AI）就是评估者，不需要任何 API。

> 可选增强：若使用方自己配了其他大模型的 key，可跑 `scripts/evaluate.py` 拿第二个模型
> 按同一 rubric 交叉打分，看分歧（某维度两边差 ≥1 分 = 假设在那里写得模棱两可）。
> 这**不是必须**的——没配 key 时单靠你自己评估即可。

### 3. 把诊断变成教练建议（核心）
打分本身是线索，不是交付物。对每个弱项（得分低、或多模型有分歧的维度），给三件套：
1. **为什么重要**——用 PDCA/可验证性的道理讲清，不是"规则要求"，而是"不这样到期就对不上账"。
2. **现在 vs 改成**——引用他原文，给一个**具体的 before→after 改写**。这是最有效的教学：
   让他看到"好的长什么样"，而不是抽象地说"要量化"。
3. 点到为止，不替他想业务内容（数字阈值留空让他填，或用占位说明，但结构给全）。

也要**指出他做得好的地方**并说明为什么好——强化好习惯和发展同样重要。

**高频高价值教练点：检验窗太长 → 过程指标。** 最常见的毛病是检验窗拉得很长，
根因往往是**盯着最终结果指标**（如总销售额、总销量这类滞后指标）——结果指标慢，所以等很久。
但真正的假设验证应该盯**过程/先导指标**（完播率、点击率、转化漏斗某一步、加购率…），
出数快、几天就能验。看到长检验窗，别只说"把日期钉死"，要问他：
"验证这个假设，有没有更快的过程指标？能不能 T+3 而不是等 2 周看最终结果？"
教会他这一招，比改十个日期都管用。

## 输出格式

教练优先。分数卡放后面当佐证，别打头。

```
## 假设体检：<一句话概括这条假设>

🎯 最该练的一点：<一句话点出最大成长项，像教练那样说>

### 照着改，假设就立住了
**1. <弱项名，如"检验时点">** ——为什么重要：<可验证性的道理，一句话>
   现在：<引用他写的（或"未填"）>
   改成：<具体 before→after 改写>

**2. ...**（一般 1-3 条，抓最关键的，别全维度罗列）

### 已经做得好的（保持）
- <哪里写得好 + 为什么好，让他下次继续这么干>

<details>分数卡（佐证）
| 维度 | 分 | 说明 |
|---|--|---|
| ... 逐维度分 ... |
评级：B 基本成立
（若跑了可选的多模型交叉验证，这里并排展示各模型分并标出分歧）
</details>

💡 带走的习惯：<一句可迁移的方法，下次他自己就能用>
（如"写完假设先自问：它能被一个具体数字、在一个具体日期，证明对或错吗？"）
```

## 4. 邀请校准反馈（重要——这是 rubric 进化的燃料）

给完评估后，**主动请评审本人确认一句**：
「这个改进建议对你有用吗？有没有指错方向、或漏了更该练的点？」

重点是**教练建议有没有帮到使用者提升**，分数只是次要佐证。
如果对方回应（"有用" / "最该练的其实是 X 不是检验时点" / "这条建议太苛刻了" 等），
就把反馈追加进校准库：

```bash
python3 scripts/log_feedback.py \
  --hypothesis "<假设原文，可截断>" \
  --ai-band "<本次评级>" --ai-total <总分> --ai-max <满分> --rubric-version <版本> \
  --verdict ok|recalibrate --comment "<对方的修正意见>" --reviewer "<评审人>"
```

- `ok` = AI 评得对（正样本）；`recalibrate` = 需校准（comment 写清哪维/几分该怎么改）。
- 这些反馈攒在 `references/calibration_feedback.jsonl`（本地、不随 skill 分发），是优化 rubric 时的金标准。
- 对方没回应就不记，别硬凑。不要替对方编校准意见。

## 边界（重要）

- 不说"这个动作该不该做"、不给业务方向；只评估"假设作为可验证命题"的质量。
- 多模型只是可选的交叉校验，不是投票表决业务对错。分歧 = 假设写得不够清楚的信号。
- rubric 是活的：每次都读文件，不要硬编码维度。

## 给维护者

- `rubric/pdca_rubric.json` — 评估标尺，自我优化的对象。
- `scripts/log_feedback.py` / `calibration_status.py` — 校准反馈记录与触发检查。
- `scripts/evaluate.py` — **可选**的多模型交叉验证（需自配 key，默认不用）。
- 自我优化与校准机制见 `references/darwin_calibration.md`。
