#!/usr/bin/env python3
import os, re, sys, shutil, hashlib, csv
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", ".")).resolve()
DEST = PROJECT_ROOT / os.environ.get("REF_DEST", "NOTES/reqs/reqfiles")
MAX_BYTES = int(os.environ.get("REF_MAX_BYTES", str(100*1024*1024)))
DENY_EXT = set((os.environ.get("REF_DENY_EXT",".apk,.aab,.ipa,.img,.bin,.rom,.iso,.qcow2,.vmdk,.elf,.exe,.dll,.dylib,.pcap")).split(","))
SKIP_DIRS = {".git",".work","venv",".venv",".idea",".vscode"}

md_link = re.compile(r'!?\\[[^\\]]*\\]\\(([^)]+)\\)')

def iter_markdown_files():
    for p in PROJECT_ROOT.rglob("*.md"):
        parts = set(p.parts)
        if parts & SKIP_DIRS: continue
        yield p

def normalize_link(base, link):
    link = link.strip()
    if link.startswith(("http://","https://","mailto:","#")): return None
    # strip anchors or query
    link = link.split("#")[0].split("?")[0]
    p = (base.parent / link).resolve()
    try:
        p.relative_to(PROJECT_ROOT)
    except ValueError:
        return None
    return p

def sha256_file(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = DEST / "_refmap.csv"
    seen = set()
    with manifest.open("w", newline="", encoding="utf-8") as mf:
        w = csv.writer(mf)
        w.writerow(["source_md","link_path","abs_src","bytes","sha256","dest_rel"])
        for md in iter_markdown_files():
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for link in md_link.findall(text):
                src = normalize_link(md, link)
                if not src or not src.exists() or not src.is_file(): continue
                if src.suffix.lower() in DENY_EXT: continue
                size = src.stat().st_size
                if size > MAX_BYTES: continue
                key = (str(src), size)
                if key in seen: continue
                seen.add(key)
                digest = sha256_file(src)
                dst_name = f"{digest[:12]}_{src.name}"
                dst_rel = Path("NOTES/reqs/reqfiles") / dst_name
                dst_abs = DEST / dst_name
                if not dst_abs.exists():
                    shutil.copy2(src, dst_abs)
                w.writerow([str(md.relative_to(PROJECT_ROOT)),
                            link,
                            str(src.relative_to(PROJECT_ROOT)),
                            size,
                            digest,
                            str(dst_rel)])
if __name__ == "__main__":
    sys.exit(main())
