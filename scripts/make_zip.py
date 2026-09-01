# -*- coding: utf-8 -*-
"""源代码打包（iCAN 其他证明材料 zip）：
包含全部源码、人物/地点库、立绘素材、脚本、README；
排除 .env（密钥）、数据库、用户照片、提交材料自身。
运行：python scripts/make_zip.py → submission/千年晤旅_源代码.zip
"""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PROJECT_ROOT

EXCLUDE_DIRS = {"__pycache__", ".git", "submission", ".smoke_tmp"}
EXCLUDE_SUFFIX = {".db", ".db-wal", ".db-shm", ".pyc", ".env"}
EXCLUDE_NAMES = {".env"}


def main():
    out = PROJECT_ROOT / "submission" / "千年晤旅_源代码.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(PROJECT_ROOT.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(PROJECT_ROOT)
            parts = rel.parts
            if any(part in EXCLUDE_DIRS for part in parts):
                continue
            if p.name in EXCLUDE_NAMES or p.suffix in EXCLUDE_SUFFIX:
                continue
            if parts and parts[0] == "assets" and parts[1:2] and parts[1] == "photos":
                continue  # 用户合影照片不打包
            zf.write(p, rel.as_posix())
            n += 1
    print(f"源码包: {out} ({out.stat().st_size/1024:.0f} KB · {n} 个文件)")


if __name__ == "__main__":
    main()
