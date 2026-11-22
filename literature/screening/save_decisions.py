"""Convert sr_work/decisions_raw.txt (reviewer returns transcribed by the lead as `num|code|why`
under `#<role>_<batch>` headers) into the per-label JSON files merge_decisions.py reads."""
import json
import os

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sr_work")
idx = json.load(open(os.path.join(base, "prompts", "index.json"), encoding="utf-8"))
items = idx if isinstance(idx, list) else idx.get("jobs", idx)
os.makedirs(os.path.join(base, "decisions"), exist_ok=True)
cur, out = None, {}
for line in open(os.path.join(base, "decisions_raw.txt"), encoding="utf-8"):
    line = line.rstrip("\n")
    if not line:
        continue
    if line.startswith("#"):
        cur = line[1:]
        out[cur] = []
        continue
    n, c, w = line.split("|", 2)
    d = {"INC": "include", "UNC": "unclear"}.get(c, "exclude")
    out[cur].append({"id": "R%05d" % int(n), "d": d, "code": c, "why": w})
for k, v in out.items():
    r, b = k.split("_")
    label = [e["label"] for e in items if e["label"].startswith(f"{r}:{b}@")][0]
    path = os.path.join(base, "decisions", label.replace(":", "_") + ".json")
    json.dump({"label": label, "decisions": v}, open(path, "w", encoding="utf-8"), indent=1)
    print(k, len(v))
