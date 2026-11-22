#!/usr/bin/env python3
"""Local dashboard for the research team.

Start it from the project root (or double-click 启动面板.bat):
    python tools/dashboard.py            # then open http://127.0.0.1:8765
    python tools/dashboard.py --open     # also opens the browser

It shows which stage the project is in, what the lead and each subagent are doing,
calls to the outside reviewers, things waiting for you, and lets you edit 00_idea/idea.md.

The page only talks to this computer (127.0.0.1). The only file it can change is
00_idea/idea.md. Activity comes from .dashboard/events.jsonl, written by
tools/dashboard_hook.py and tools/ask_reviewer.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / ".dashboard" / "events.jsonl"
IDEA = ROOT / "00_idea" / "idea.md"
PAGE = Path(__file__).resolve().parent / "dashboard.html"
PORT = 8765
STALE_TASK_S = 45 * 60
STALE_LEAD_S = 15 * 60
SKIP_DIRS = {".dashboard", ".git", ".venv", "__pycache__", "node_modules", "code", "hf", ".claude"}

ROSTER = [
    ("lead", "组长", "调度、整合、在关卡向你汇报"),
    ("literature-scout", "文献调研员", "查论文、代码、数据集，判断新颖性"),
    ("researcher", "研究员", "理论证明和实验"),
    ("writer", "写手", "写论文、改论文"),
    ("gpt", "GPT 审稿人", "外部独立审查（Codex）"),
    ("gemini", "Gemini 审稿人", "外部独立审查（Antigravity）"),
    ("ars", "ARS 插件", "文献综述、筛选、核查、模拟审稿"),
]


def read_events(limit: int = 8000) -> list[dict]:
    if not EVENTS.is_file():
        return []
    try:
        lines = EVENTS.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            ev = json.loads(line)
            if isinstance(ev, dict) and "ts" in ev:
                out.append(ev)
        except ValueError:
            continue
    return out


def parse_status() -> dict:
    """Read the stage table and the current-stage line from STATUS.md."""
    path = ROOT / "STATUS.md"
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    m = re.search(r"\*\*当前阶段[:：]\*\*\s*(.+)", text)
    stages = []
    for row in re.finditer(r"^\|\s*(\d)\s+([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", text, re.M):
        raw = row.group(3)
        if "✅" in raw or "完成" in raw:
            state = "done"
        elif "🚦" in raw or "等待" in raw or "待你" in raw:
            state = "gate"
        elif "返工" in raw:
            state = "rework"
        elif "🔄" in raw or "进行" in raw:
            state = "active"
        else:
            state = "todo"
        gate = row.group(4).strip()
        stages.append({
            "n": int(row.group(1)), "name": row.group(2).strip(), "state": state,
            "label": re.sub(r"[⬜✅🔄🚦]\s*", "", raw).strip(),
            "gate": re.sub(r"[🚦—\-]\s*", "", gate).strip(),
        })
    decisions = re.findall(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|", text, re.M)
    return {
        "current": m.group(1).replace("`", "").strip() if m else "",
        "stages": stages,
        "last_decision": {"date": decisions[-1][0], "text": decisions[-1][1].strip()} if decisions else None,
    }


def build_activity(now: float) -> dict:
    events = read_events()
    tasks: dict[str, dict] = {}
    by_agent: dict[str, dict] = {}
    skills: dict[str, dict] = {}
    reviews: dict[str, dict] = {}
    lead = {"state": "unknown", "since": None, "last_action": None, "notice": None, "session": None}

    def lead_touch(ev: dict) -> None:
        lead["session"] = ev.get("session")
        lead["notice"] = None
        if lead["state"] != "working":
            lead["state"], lead["since"] = "working", ev["ts"]

    for i, ev in enumerate(events):
        name, ts, tool = ev.get("event"), ev["ts"], ev.get("tool")
        agent_id = ev.get("agent_id")

        if name == "UserPromptSubmit":
            lead.update(state="working", since=ts, session=ev.get("session"), notice=None)
        elif name == "Stop":
            lead.update(state="waiting", since=ts, session=ev.get("session"), notice=None)
        elif name == "Notification":
            lead["notice"] = {"text": ev.get("message") or "需要你看一下 Claude 窗口", "ts": ts}
        elif name == "PreToolUse":
            action = {"tool": tool, "target": ev.get("target", ""), "ts": ts}
            if agent_id and agent_id in by_agent:
                by_agent[agent_id]["last_action"] = action
                by_agent[agent_id]["last_ts"] = ts
                if ev.get("handback"):
                    by_agent[agent_id]["result"] = ev["handback"]
            elif not agent_id:
                lead_touch(ev)
                lead["last_action"] = action
                if tool in ("Agent", "Task"):
                    key = ev.get("tool_use_id") or f"task-{i}"
                    tasks[key] = {
                        "id": key, "member": ev.get("subagent_type") or "general-purpose",
                        "description": ev.get("description") or "（没有任务说明）", "task": ev.get("task", ""),
                        "started": ts, "ended": None, "status": "running", "result": "",
                        "agent_id": None, "last_action": None, "last_ts": ts,
                        "session": ev.get("session"), "background": bool(ev.get("background")),
                    }
                elif tool == "Skill":
                    key = ev.get("tool_use_id") or f"skill-{i}"
                    skills[key] = {
                        "id": key, "member": "ars" if "academic-research-skills" in (ev.get("skill") or "") else "skill",
                        "description": (ev.get("skill") or "skill").split(":")[-1],
                        "task": ev.get("skill_args", ""), "started": ts, "ended": None,
                        "status": "running", "result": "", "last_action": None, "last_ts": ts,
                    }
        elif name == "SubagentStart" and agent_id:
            kind = ev.get("agent_type") or ""
            # "soft" = closed only because the launch call returned; the events can arrive in either order
            open_tasks = [t for t in tasks.values()
                          if (t["status"] == "running" or t.get("soft")) and not t["agent_id"]
                          and t["session"] == ev.get("session")]
            match = next((t for t in open_tasks if t["member"] == kind), None) or (open_tasks[0] if open_tasks and not kind else None)
            if match is None:
                key = f"agent-{agent_id}"
                match = tasks[key] = {
                    "id": key, "member": kind or "subagent", "description": "（没有记录到任务说明）", "task": "",
                    "started": ts, "ended": None, "status": "running", "result": "", "agent_id": None,
                    "last_action": None, "last_ts": ts, "session": ev.get("session"), "background": False,
                }
            match.update(agent_id=agent_id, last_ts=ts, status="running", ended=None, soft=False)
            by_agent[agent_id] = match
        elif name == "SubagentStop" and agent_id in by_agent:
            t = by_agent[agent_id]
            t.update(status="done", ended=ts, result=ev.get("result") or t.get("result", ""), last_ts=ts)
        elif name in ("PostToolUse", "PostToolUseFailure") and not agent_id:
            lead_touch(ev)
            key = ev.get("tool_use_id")
            failed = name == "PostToolUseFailure"
            if tool in ("Agent", "Task") and key in tasks:
                t = tasks[key]
                if failed:
                    t.update(status="failed", ended=ts, result=ev.get("error", ""))
                elif not t["agent_id"] and t["status"] == "running" and not t["background"]:
                    t.update(status="done", ended=ts, soft=True)  # no start event seen (yet) for it
            elif tool == "Skill" and key in skills:
                # the skill's instructions are loaded; the lead then carries them out itself
                skills[key].update(status="failed" if failed else "done", ended=ts)
        elif name == "ReviewerStart":
            reviews[ev.get("run_id", f"rev-{i}")] = {
                "id": ev.get("run_id", f"rev-{i}"), "member": ev.get("reviewer", "gpt"),
                "description": (
                    f"讨论：{ev.get('run_id', '').split('_')[1] if ev.get('run_id', '').count('_') >= 3 else ''}"
                    if ev.get("task_kind") == "discuss"
                    else f"{'独立推导' if ev.get('task_kind') == 'derive' else ev.get('task_kind', '') + ' 审查'}："
                         f"{', '.join(ev.get('files', []))}"
                ),
                "task": "", "started": ts, "ended": None, "status": "running", "result": "",
                "last_action": None, "last_ts": ts,
            }
        elif name == "ReviewerEnd" and ev.get("run_id") in reviews:
            code = ev.get("exit_code")
            status = "done" if code == 0 else "manual" if code == 2 else "failed"
            reviews[ev["run_id"]].update(status=status, ended=ts, result=ev.get("note", ""), last_ts=ts)

    items = list(tasks.values()) + list(skills.values()) + list(reviews.values())
    for t in items:
        if t["status"] == "running" and now - (t.get("last_ts") or t["started"]) > STALE_TASK_S:
            t["status"] = "stale"
        t["duration"] = round((t["ended"] or now) - t["started"])
    running = [t for t in items if t["status"] == "running"]

    if lead["state"] == "working" and not running and lead["last_action"] and now - lead["last_action"]["ts"] > STALE_LEAD_S:
        lead["state"] = "stale"
    if lead["state"] == "working" and running and lead["last_action"] and now - lead["last_action"]["ts"] > 60:
        lead["state"] = "delegating"

    items.sort(key=lambda t: t["started"], reverse=True)
    return {"lead": lead, "items": items[:60], "has_events": bool(events),
            "last_event": events[-1]["ts"] if events else None}


def pending_downloads() -> int:
    path = ROOT / "resources" / "DOWNLOAD_LIST.md"
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
               if line.startswith("|") and "待批准" in line and "已批准" not in line.split("|")[-2])


def unanswered_outbox() -> list[str]:
    outbox, inbox = ROOT / "reviews" / "outbox", ROOT / "reviews" / "inbox"
    if not outbox.is_dir():
        return []
    have = {p.stem for p in inbox.glob("*")} if inbox.is_dir() else set()
    return sorted(p.name for p in outbox.glob("*.md") if p.stem not in have)


def idea_is_blank() -> bool:
    if not IDEA.is_file():
        return True
    text = IDEA.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"##\s*1\.[^\n]*\n(.*?)(?=\n##\s|\Z)", text, re.S)
    body = m.group(1) if m else text
    body = "\n".join(l for l in body.splitlines() if not l.strip().startswith(("（", "(", ">")))
    return not body.strip()


def recent_files(limit: int = 10) -> list[dict]:
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = Path(base) / f
            try:
                found.append((p.stat().st_mtime, p))
            except OSError:
                pass
    found.sort(reverse=True)
    return [{"path": p.relative_to(ROOT).as_posix(), "mtime": m} for m, p in found[:limit]]


def build_state() -> dict:
    now = time.time()
    status = parse_status()
    activity = build_activity(now)
    lead = activity["lead"]

    todo = []
    if lead.get("notice"):
        todo.append({"kind": "attention", "text": f"Claude 窗口需要你处理：{lead['notice']['text']}"})
    for s in status["stages"]:
        if s["state"] == "gate":
            todo.append({"kind": "gate", "text": f"关卡等你决定：阶段 {s['n']} {s['name']}。在 Claude 里回复 /next 或写下返工意见。"})
    n = pending_downloads()
    if n:
        todo.append({"kind": "download", "text": f"有 {n} 项下载等你批准（resources/DOWNLOAD_LIST.md）"})
    for name in unanswered_outbox():
        todo.append({"kind": "optional", "text": f"可选：把 reviews/outbox/{name} 粘贴到 Gemini 桌面版做加强审查"})
    if idea_is_blank():
        todo.append({"kind": "start", "text": "先在下方写下你的想法并保存，然后在 Claude 里输入 /kickoff"})

    members = []
    for key, label, role in ROSTER:
        mine = [t for t in activity["items"] if t["member"] == key]
        members.append({"key": key, "label": label, "role": role,
                        "running": [t for t in mine if t["status"] == "running"],
                        "stale": [t for t in mine if t["status"] == "stale"],
                        "last": next((t for t in mine if t["status"] not in ("running", "stale")), None),
                        "count_done": sum(1 for t in mine if t["status"] == "done")})
    known = {k for k, _, _ in ROSTER}
    others = sorted({t["member"] for t in activity["items"] if t["member"] not in known})
    for key in others:
        mine = [t for t in activity["items"] if t["member"] == key]
        members.append({"key": key, "label": key, "role": "其他子 agent",
                        "running": [t for t in mine if t["status"] == "running"],
                        "stale": [t for t in mine if t["status"] == "stale"],
                        "last": next((t for t in mine if t["status"] not in ("running", "stale")), None),
                        "count_done": sum(1 for t in mine if t["status"] == "done")})

    return {
        "now": now, "project": ROOT.name, "status": status, "lead": lead, "members": members,
        "items": activity["items"], "todo": todo, "files": recent_files(),
        "tracking": {"has_events": activity["has_events"], "last_event": activity["last_event"]},
    }


def idea_payload() -> dict:
    if IDEA.is_file():
        return {"content": IDEA.read_text(encoding="utf-8", errors="replace"), "mtime": IDEA.stat().st_mtime}
    return {"content": "", "mtime": 0}


class Handler(BaseHTTPRequestHandler):
    server_version = "ResearchDashboard/1.0"

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def local_only(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def send_json(self, obj, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.local_only():
            return self.send_json({"error": "local only"}, 403)
        path = self.path.split("?")[0]
        if path == "/":
            body = PAGE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/state":
            self.send_json(build_state())
        elif path == "/api/idea":
            self.send_json(idea_payload())
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        # The custom header cannot be sent by another website without a permission check
        # that this server never grants, so only this page can save.
        if not self.local_only() or self.headers.get("X-Dashboard") != "1":
            return self.send_json({"error": "forbidden"}, 403)
        if self.path.split("?")[0] != "/api/idea":
            return self.send_json({"error": "not found"}, 404)
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 1_000_000:
            return self.send_json({"error": "内容为空或超过 1 MB"}, 400)
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            content, base, force = data["content"], float(data.get("base_mtime") or 0), bool(data.get("force"))
            assert isinstance(content, str)
        except Exception:
            return self.send_json({"error": "bad request"}, 400)
        current = idea_payload()
        if not force and current["mtime"] and abs(current["mtime"] - base) > 0.001:
            return self.send_json({"error": "conflict", **current}, 409)
        IDEA.parent.mkdir(parents=True, exist_ok=True)
        tmp = IDEA.with_suffix(".md.tmp")
        tmp.write_text(content, encoding="utf-8", newline="\n")
        tmp.replace(IDEA)
        self.send_json({"ok": True, "mtime": IDEA.stat().st_mtime})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--open", action="store_true", help="open the dashboard in your browser")
    args = ap.parse_args()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        print(f"端口 {args.port} 已被占用：面板可能已经在运行，直接打开 http://127.0.0.1:{args.port}")
        if args.open:
            webbrowser.open(f"http://127.0.0.1:{args.port}")
        return 0
    url = f"http://127.0.0.1:{args.port}"
    print(f"研究团队面板已启动：{url}   （关闭这个窗口即可停止）", flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
