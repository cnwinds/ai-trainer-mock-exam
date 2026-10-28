# -*- coding: utf-8 -*-
"""校验题库：python tools/validate.py [--dump kp]"""
import json, sys, pathlib, collections

BANK = pathlib.Path(__file__).resolve().parents[1] / "data" / "bank"
KPS = {"ethics", "law", "office", "security", "bpm", "product", "pm", "training", "ml", "dl", "algo", "data", "llm", "aisys"}
errs, ids, all_q = [], {}, []
for f in sorted(BANK.glob("*.json")):
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        errs.append(f"{f.name}: JSON 解析失败 {e}")
        continue
    for q in data:
        qid = q.get("id")
        where = f"{f.name}:{qid}"
        if qid in ids:
            errs.append(f"重复 id {qid}（{ids[qid]} / {f.name}）")
        ids[qid] = f.name
        t = q.get("type")
        if q.get("kp") not in KPS:
            errs.append(f"{where} kp 非法 {q.get('kp')}")
        if t in ("single", "multi"):
            if len(q.get("options", [])) != 4:
                errs.append(f"{where} options 数量 {len(q.get('options', []))}")
            a = q.get("answer", "")
            if not a or any(c not in "ABCD" for c in a) or (t == "single" and len(a) != 1) or (t == "multi" and (len(a) < 2 or a != "".join(sorted(set(a))))):
                errs.append(f"{where} answer 非法 {a}")
        elif t == "judge":
            if q.get("answer") not in ("T", "F"):
                errs.append(f"{where} judge answer {q.get('answer')}")
        elif t == "short":
            s = sum(r.get("score", 0) for r in q.get("rubric", []))
            if s != q.get("score", 10):
                errs.append(f"{where} rubric 合计 {s}")
        elif t == "case":
            s = sum(r.get("score", 0) for r in q.get("checklist", []))
            if s != 100:
                errs.append(f"{where} checklist 合计 {s}")
        else:
            errs.append(f"{where} type 非法 {t}")
        if t in ("judge", "single", "multi") and not (q.get("explain") and q.get("thinking")):
            errs.append(f"{where} 缺 explain/thinking")
        all_q.append(q)

print("题目总数", len(all_q))
print("按题型", dict(collections.Counter(q["type"] for q in all_q)))
print("按知识点", dict(collections.Counter(q["kp"] for q in all_q)))
print("单选答案分布", dict(collections.Counter(q["answer"] for q in all_q if q["type"] == "single")))
print("判断答案分布", dict(collections.Counter(q["answer"] for q in all_q if q["type"] == "judge")))
print("错误", len(errs))
for e in errs:
    print("  -", e)

if "--dump" in sys.argv:
    kp = sys.argv[sys.argv.index("--dump") + 1]
    for q in all_q:
        if q["kp"] == kp and q.get("src") == "新编" and q["type"] in ("judge", "single", "multi"):
            opts = " | ".join(f"{'ABCD'[i]}.{o}" for i, o in enumerate(q.get("options", [])))
            print(f"\n[{q['id']}] {q['stem']}\n  {opts}\n  答案={q['answer']}  {q['explain'][:120]}")
