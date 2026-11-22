#!/usr/bin/env python3
"""Record what the team is doing, for the dashboard.

Claude Code runs this script on its own events (a tool is about to run, a subagent
started or stopped, the lead finished a turn, ...) and passes the event as JSON on stdin.
The script appends one compact line per event to .dashboard/events.jsonl.

It only records. It never blocks or changes anything, and it always exits 0.
What it does NOT store: the text you type, file contents, or full command lines.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / ".dashboard"
LOG = LOG_DIR / "events.jsonl"
MAX_BYTES = 8 * 1024 * 1024  # start a fresh file past 8 MB (the old one is kept as events.old.jsonl)


def clip(value, n: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def target_of(tool: str, inp: dict) -> str:
    """A short, human-readable hint of what a tool call is working on."""
    if not isinstance(inp, dict):
        return ""
    for key in ("file_path", "path", "notebook_path"):
        if inp.get(key):
            p = str(inp[key]).replace("\\", "/")
            root = str(ROOT).replace("\\", "/")
            return clip(p[len(root) + 1:] if p.lower().startswith(root.lower() + "/") else p, 120)
    if tool in ("Bash", "PowerShell"):
        # the human-readable description if there is one, otherwise only the program name
        return clip(inp.get("description") or str(inp.get("command", "")).strip().split(" ")[0], 100)
    if tool in ("WebSearch",):
        return clip(inp.get("query"), 100)
    if tool in ("WebFetch",):
        return clip(inp.get("url"), 100)
    if tool in ("Grep", "Glob"):
        return clip(inp.get("pattern"), 80)
    if tool == "Skill":
        return clip(inp.get("skill"), 80)
    return ""


def main() -> None:
    # read bytes and decode as UTF-8 ourselves: on Chinese Windows the default would be GBK
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    data = json.loads(raw) if raw.strip() else {}
    if not isinstance(data, dict):
        return
    name = data.get("hook_event_name") or ""
    tool = data.get("tool_name") or ""
    inp = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}

    ev = {"ts": round(time.time(), 2), "event": name, "session": clip(data.get("session_id"), 40)}
    for key in ("agent_id", "agent_type", "tool_use_id"):
        if data.get(key):
            ev[key] = clip(data[key], 80)
    if tool:
        ev["tool"] = tool
        ev["target"] = target_of(tool, inp)
    if tool in ("Agent", "Task"):
        ev["subagent_type"] = clip(inp.get("subagent_type") or "general-purpose", 60)
        ev["description"] = clip(inp.get("description"), 120)
        ev["task"] = clip(inp.get("prompt"), 600)
        ev["background"] = bool(inp.get("run_in_background"))
    if tool == "SubagentHandback":
        # a subagent handing its final report back to the lead: keep a short excerpt as its result
        texts = [v for v in inp.values() if isinstance(v, str)]
        ev["handback"] = clip(max(texts, key=len) if texts else "", 600)
    if tool == "Skill":
        ev["skill"] = clip(inp.get("skill"), 80)
        ev["skill_args"] = clip(inp.get("args"), 200)
    if name == "SubagentStop":
        ev["result"] = clip(data.get("last_assistant_message"), 600)
    if name == "Notification":
        ev["message"] = clip(data.get("message"), 200)
        ev["kind"] = clip(data.get("notification_type"), 60)
    if name in ("PostToolUseFailure",):
        ev["error"] = clip(data.get("error"), 300)

    LOG_DIR.mkdir(exist_ok=True)
    try:
        if LOG.exists() and LOG.stat().st_size > MAX_BYTES:
            LOG.replace(LOG_DIR / "events.old.jsonl")
    except OSError:
        pass
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # recording must never get in the way of the work
    sys.exit(0)
