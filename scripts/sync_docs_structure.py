#!/usr/bin/env python3
import json
import os
from pathlib import Path

ROOT = Path(".").resolve()
INFO = ROOT / "plugin_info" / "info.json"
DOCS = ROOT / "docs"
SRC_LANG = os.environ.get("SOURCE_LANG", "fr_FR")

data = json.loads(INFO.read_text(encoding="utf-8"))
langs = data.get("language", [])

src_dir = DOCS / SRC_LANG
if not src_dir.exists():
    raise SystemExit(f"Missing source docs folder: {src_dir}")

for lang in langs:
    if lang == SRC_LANG:
        continue
    dst_dir = DOCS / lang
    dst_dir.mkdir(parents=True, exist_ok=True)

    for src in src_dir.rglob("*.md"):
        rel = src.relative_to(src_dir)
        dst = dst_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Create only if missing (never overwrite)
        if not dst.exists():
            fr = src.read_text(encoding="utf-8")
            dst.write_text(
                f"<!-- AUTO_TRANSLATED source={SRC_LANG} src_sha256=TODO out_sha256=TODO -->\n\n{fr}",
                encoding="utf-8",
            )
            print(f"Created {dst}")
