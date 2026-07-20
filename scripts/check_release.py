#!/usr/bin/env python3
"""阻止客户身份信息和本地生成物进入标准发布版本。"""

from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "__pycache__", "official-docs"}
SKIP_FILES = {"config.ini", "CHANGE_log.md"}
BANNED_TERMS = (
    "广东省政务服务和数据管理" + "局",
    "广东省政数" + "局",
    "粤政" + "数",
    "粤政" + "易",
)


def main():
    findings = []
    for path in SKILL_ROOT.rglob("*"):
        if not path.is_file() or path.name in SKIP_FILES or any(part in SKIP_PARTS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for term in BANNED_TERMS:
                if term in line:
                    findings.append(f"{path.relative_to(SKILL_ROOT)}:{line_number}: {term}")

    if findings:
        print("发布检查失败：发现客户强相关内容")
        print("\n".join(findings))
        raise SystemExit(1)
    print("发布检查通过：未发现已登记的客户强相关内容")


if __name__ == "__main__":
    main()
