# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

## 0. Project Spec

**每次对话开始时，必须先读取 `DEV_SPEC.md`。**

- 所有开发工作以 DEV_SPEC.md 中的架构设计和阶段规划为准，不得自行引入文档中未决策的技术或模式。
- 如果开发过程中发现文档描述与实际实现有出入，以实际实现为准，并同步修正文档。
- 在 PowerShell 中读取中文项目文件时必须显式使用 UTF-8，例如 `Get-Content -Raw -Encoding UTF8 -LiteralPath DEV_SPEC.md`。不要因为默认终端解码显示异常就判断源码或文档乱码。
- 项目 Python 环境由 `uv` / `.venv` 管理。验证时优先使用 `uv run python ...`，例如 `uv run python -m compileall app.py fastdata`。
- 在 Codex 沙箱中，普通权限下直接运行 `uv run ...` 可能因用户目录 uv cache 初始化失败，直接运行 `.venv\Scripts\python.exe` 可能因 uv trampoline 权限被拒绝。此时应说明这是沙箱权限问题，并按授权方式重跑 `uv run ...`，不要误判为项目环境缺失。

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
