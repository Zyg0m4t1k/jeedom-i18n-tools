#!/usr/bin/env python3
import os, json, re, hashlib
from pathlib import Path
import requests

ROOT = Path(".").resolve()
INFO = ROOT / "plugin_info" / "info.json"
DOCS = ROOT / "docs"
SRC_LANG = os.environ.get("SOURCE_LANG", "fr_FR")

# 🔥 FIX : strip() pour éviter les espaces invisibles (cause 403)
DEEPL_KEY = (os.environ.get("DEEPL_API_KEY") or "").strip()

if not DEEPL_KEY:
    raise SystemExit("Missing DEEPL_API_KEY")

data = json.loads(INFO.read_text(encoding="utf-8"))
langs = data.get("language", [])

src_dir = DOCS / SRC_LANG
if not src_dir.exists():
    raise SystemExit(f"Missing source docs folder: {src_dir}")

DEEPL_MAP = {
    "en_US": "EN-US",
    "en_GB": "EN-GB",
    "de_DE": "DE",
    "es_ES": "ES",
    "it_IT": "IT",
    "pt_PT": "PT-PT",
    "nl_NL": "NL",
    "pl_PL": "PL",
    "ru_RU": "RU",
}

MARKER_RE = re.compile(
    r"^\s*<!--\s*AUTO_TRANSLATED\s+source=(?P<src>[A-Za-z_]+)\s+src_sha256=(?P<srcsha>[0-9a-fA-F]+|TODO)\s+out_sha256=(?P<outsha>[0-9a-fA-F]+|TODO)\s*-->\s*\n?",
    re.MULTILINE,
)

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def protect_code_blocks(text: str):
    blocks = []
    def repl(m):
        blocks.append(m.group(0))
        return f"__CODE_BLOCK_{len(blocks)-1}__"
    protected = re.sub(r"```[\s\S]*?```", repl, text)
    return protected, blocks

def restore_code_blocks(text: str, blocks):
    for i, b in enumerate(blocks):
        text = text.replace(f"__CODE_BLOCK_{i}__", b)
    return text

def deepl_translate(text: str, target_lang: str) -> str:
    # DeepL endpoints:
    # - API Free: https://api-free.deepl.com
    # - API Pro : https://api.deepl.com
    #
    # Important (2026): legacy authentication by sending `auth_key` in the body/query
    # is deprecated and can return 403. Use the `DeepL-Auth-Key` header instead.
    key = DEEPL_KEY
    base_url = (os.environ.get("DEEPL_API_URL") or "").strip()
    if not base_url:
        # Heuristic: API Free keys usually end with ':fx'
        base_url = "https://api-free.deepl.com" if key.endswith(":fx") else "https://api.deepl.com"

    url = base_url.rstrip("/") + "/v2/translate"
    headers = {"DeepL-Auth-Key": key}

    payload = {
        "text": text,
        "target_lang": target_lang,
    }

    r = requests.post(url, data=payload, headers=headers, timeout=90)

    # 🔥 DEBUG AMÉLIORÉ
    if r.status_code >= 400:
        print("DeepL endpoint:", url)
        print("DeepL error:", r.status_code)
        print("Response:", r.text[:1000])

    r.raise_for_status()
    return r.json()["translations"][0]["text"]


for lang in langs:
    if lang == SRC_LANG:
        continue

    target = DEEPL_MAP.get(lang, lang.split("_")[0].upper())
    dst_dir = DOCS / lang
    if not dst_dir.exists():
        continue

    for src in src_dir.rglob("*.md"):
        rel = src.relative_to(src_dir)
        dst = dst_dir / rel
        if not dst.exists():
            continue

        cur = dst.read_text(encoding="utf-8")

        m = MARKER_RE.match(cur)
        if not m:
            continue

        cur_wo_marker = MARKER_RE.sub("", cur, count=1)
        cur_out_sha = sha256_text(cur_wo_marker)

        marker_out_sha = m.group("outsha")
        if marker_out_sha not in ("TODO", "") and cur_out_sha.lower() != marker_out_sha.lower():
            continue

        fr = src.read_text(encoding="utf-8")
        fr_sha = sha256_text(fr)

        marker_src_sha = m.group("srcsha")
        if marker_src_sha not in ("TODO", "") and fr_sha.lower() == marker_src_sha.lower():
            continue

        protected, blocks = protect_code_blocks(fr)
        translated = deepl_translate(protected, target)
        translated = restore_code_blocks(translated, blocks)

        out_sha = sha256_text(translated)
        marker = f"<!-- AUTO_TRANSLATED source={SRC_LANG} src_sha256={fr_sha} out_sha256={out_sha} -->\n\n"

        dst.write_text(marker + translated, encoding="utf-8")
        print(f"Translated {dst} -> {lang}")
