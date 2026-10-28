# -*- coding: utf-8 -*-
"""从 pi 的 models.json 读取模型配置，写入 exam-app/config.json 的 llm 段。

python tools/import_pi_model.py                 # 默认 glm-5.3-flash
python tools/import_pi_model.py qwen3.8-flash   # 其他模型 id
python tools/import_pi_model.py glm-5.3-flash --models C:/path/models.json
"""
import json, sys, pathlib

APP = pathlib.Path(__file__).resolve().parents[1]
CFG = APP / "config.json"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    model_id = args[0] if args else "glm-5.3-flash"
    src = pathlib.Path.home() / ".pi" / "agent" / "models.json"
    if "--models" in sys.argv:
        src = pathlib.Path(sys.argv[sys.argv.index("--models") + 1])
    providers = json.loads(src.read_text(encoding="utf-8"))["providers"]
    for name, p in providers.items():
        for m in p.get("models", []):
            if m["id"] == model_id:
                cfg = json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
                llm = cfg.setdefault("llm", {})
                llm.update({"base_url": p["baseUrl"].rstrip("/"), "api_key": p.get("apiKey", ""), "model": m["id"],
                            "max_tokens": min(int(m.get("maxTokens", 8192)), 16384)})
                llm.setdefault("auto_grade", True)
                CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"已写入 {CFG}：provider={name} model={m['id']} base_url={p['baseUrl']}")
                return
    sys.exit(f"在 {src} 中没有找到模型 {model_id}")


if __name__ == "__main__":
    main()
