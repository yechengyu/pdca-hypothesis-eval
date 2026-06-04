# PDCA 假设评估器（pdca-hypothesis-eval）

一个可分发的 Claude Code 技能：把一个**假设**打磨成**可验证的命题**。
你直接把假设贴给它，它按一套 rubric 给假设的**方法论质量**打分（可证伪 / 可量化 /
检验设计 / 干扰控制 / 数据可复核 / 动作具体），并给出改进建议——
**只评估"这个假设立不立得住、怎么验证"，不替你判断业务方向对不对。**

**重点是教练，不是裁判**：每次评估都告诉你哪里弱、为什么弱、照着怎么改、下次怎么自己避开，
帮你长出"会写可验证假设"的能力。

## 安装

把本仓库放进你的 AI IDE 的 skills 目录（Claude Code 等），重启会话即可。
技能触发词：「评估这条假设」「我这个假设打几分」「这个假设成立吗」「PDCA 打分」等。

**零依赖、零 key**：运行 skill 的 AI（你 IDE 里的模型）直接按 rubric 评估，
不连任何数据库、不需要联网、不需要任何 API key。

## 可选：多模型交叉验证

想用外部大模型交叉打分、看分歧的话，在仓库根目录建一个 `.env`（已 gitignore）填 key，
再跑 `scripts/evaluate.py`。**完全可选**——不配也能用。

```
ARK_API_KEY=...        # 火山方舟（可选）
DEEPSEEK_API_KEY=...   # DeepSeek（可选）
```

## 结构

```
pdca-eval-skill/
├── SKILL.md                      技能主体（触发 / 流程 / 输出格式）
├── rubric/pdca_rubric.json       评估标尺（可编辑、可进化）
├── scripts/log_feedback.py       校准反馈记录
├── scripts/calibration_status.py 优化触发检查
├── scripts/evaluate.py           可选的多模型交叉验证
└── references/darwin_calibration.md  自我优化与校准计划
```

## 自我进化

rubric 不是写死的。`references/darwin_calibration.md` 描述了如何用达尔文式优化，
依据**人工金标准打分**持续校准这套 rubric，让 AI 的评分越来越接近资深评审的判断。
