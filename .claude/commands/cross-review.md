---
description: 让 GPT 和 Gemini 独立审查某个文件
argument-hint: <文件路径> [审查类型：novelty / proof / plan / paper]
---

按 CLAUDE.md"外部审稿"一节，用 `python tools/ask_reviewer.py` 让 GPT 和 Gemini 分别独立审查：$ARGUMENTS

两条命令同时在后台运行。都完成后，把汇总写进 `reviews/`，并用中文告诉我：两个模型的共识问题、分歧点、总体结论，以及你建议怎么处理。不要自动修改被审查的文件，等我决定。

如果某个模型无法自动调用，告诉我 `reviews/outbox/` 里哪个文件需要我手动粘贴、回答该存到 `reviews/inbox/` 的哪个文件名。
