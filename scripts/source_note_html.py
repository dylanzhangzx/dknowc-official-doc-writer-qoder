#!/usr/bin/env python3
"""生成素材来源说明 HTML。"""

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_DOCS_DIR = SKILL_ROOT / "official-docs"
INPUT_DIR = OFFICIAL_DOCS_DIR / "input"
OUTPUT_DIR = OFFICIAL_DOCS_DIR / "output"
SEARCH_RESULTS_DIR = OFFICIAL_DOCS_DIR / "search-results"
ALLOWED_INPUT_DIRS = (INPUT_DIR, OUTPUT_DIR, SEARCH_RESULTS_DIR)


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_input_json(file_path: str) -> Path:
    raw_path = Path(file_path).expanduser()
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    elif raw_path.parent == Path("."):
        resolved = (INPUT_DIR / raw_path.name).resolve()
    else:
        resolved = (SKILL_ROOT / raw_path).resolve()

    if resolved.suffix.lower() != ".json":
        raise ValueError(f"只允许读取 JSON 文件: {file_path}")
    if not any(is_relative_to(resolved, allowed.resolve()) for allowed in ALLOWED_INPUT_DIRS):
        raise ValueError(f"输入文件必须位于 skill 工作目录内: {file_path}")
    if not resolved.exists():
        raise FileNotFoundError(f"输入文件不存在: {resolved}")
    return resolved


def resolve_output_html(file_path: str, title: str) -> Path:
    if file_path:
        raw_path = Path(file_path).expanduser()
        if raw_path.is_absolute():
            resolved = raw_path.resolve()
        elif raw_path.parent == Path("."):
            resolved = (OUTPUT_DIR / raw_path.name).resolve()
        else:
            resolved = (SKILL_ROOT / raw_path).resolve()
    else:
        resolved = (OUTPUT_DIR / f"{safe_filename(title)}_素材来源说明.html").resolve()

    if resolved.suffix.lower() not in (".html", ".htm"):
        raise ValueError("输出文件必须是 .html 或 .htm")
    if not is_relative_to(resolved, OUTPUT_DIR.resolve()):
        raise ValueError(f"输出文件必须位于 official-docs/output/: {file_path}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return unique_output_path(resolved)


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for idx in range(1, 1000):
        candidate = path.with_name(f"{stem}_v{idx}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError("无法生成不重名的输出文件")


def safe_filename(text: str) -> str:
    clean = re.sub(r'[\\/:*?"<>|\s]+', "_", text.strip())
    clean = clean.strip("_")
    return clean[:80] or "素材来源说明"


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def normalize_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]


def render_kb_links(knowledge_bases):
    items = []
    for index, item in enumerate(normalize_list(knowledge_bases), 1):
        label = item.get("label") or item.get("purpose") or item.get("query") or f"知识专库链接{index}"
        url = item.get("url") or item.get("knowledgeBase")
        if not url:
            continue
        items.append(
            f'<a class="kb-link" href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
            f'<span>{esc(label)}</span><small>点击打开</small></a>'
        )
    if not items:
        return '<p class="empty">未提供知识专库链接。</p>'
    return '<div class="kb-grid">' + "\n".join(items) + '</div>'


def render_material_card(item, index):
    material_type = item.get("type") or item.get("素材类型") or "核心素材"
    name = item.get("material_name") or item.get("材料名称") or item.get("title") or item.get("文章标题") or f"素材{index}"
    source = item.get("source") or item.get("来源") or item.get("publisher") or ""
    date = item.get("date") or item.get("发布日期") or item.get("time") or ""
    section = item.get("section") or item.get("正文对应") or ""
    support = item.get("support") or item.get("支撑内容") or ""
    verify = item.get("verify") or item.get("核验提示") or ""
    source_text = "，".join(part for part in [source, date] if part)

    verify_html = f'<div class="verify"><b>核验提示：</b>{esc(verify)}</div>' if verify else ""
    return f"""
    <article class="material-card">
      <div class="card-top">
        <span class="badge">{esc(material_type)}</span>
        <span class="index">#{index}</span>
      </div>
      <h3>{esc(name)}</h3>
      <dl>
        <div><dt>来源</dt><dd>{esc(source_text or "未标注")}</dd></div>
        <div><dt>正文对应</dt><dd>{esc(section or "未标注")}</dd></div>
        <div><dt>支撑内容</dt><dd>{esc(support or "未标注")}</dd></div>
      </dl>
      {verify_html}
    </article>
    """


def render_materials(materials):
    material_items = normalize_list(materials)
    if not material_items:
        return '<p class="empty">未提供素材使用情况。</p>'

    groups = {}
    for item in material_items:
        group = item.get("type") or item.get("素材类型") or "核心素材"
        groups.setdefault(group, []).append(item)

    html_parts = []
    index = 1
    for group_name, group_items in groups.items():
        html_parts.append(f'<section class="material-group"><h2>{esc(group_name)}</h2><div class="cards">')
        for item in group_items:
            html_parts.append(render_material_card(item, index))
            index += 1
        html_parts.append('</div></section>')
    return "\n".join(html_parts)


def render_checks(checks):
    check_items = normalize_list(checks)
    if not check_items:
        return '<p class="empty">暂无需人工核验信息。</p>'
    lis = "\n".join(f"<li>{esc(item)}</li>" for item in check_items)
    return f"<ol>{lis}</ol>"


def render_html(data):
    title = data.get("title") or data.get("标题") or "素材来源说明"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = data.get("summary") or "本说明用于回看本次深知搜索召回材料，核验正文中的政策、数据和案例依据。正式正文不嵌入链接，需核验时可通过知识专库链接回看原始材料。"
    knowledge_bases = data.get("knowledge_bases") or data.get("knowledgeBases") or data.get("知识专库链接") or []
    materials = data.get("materials") or data.get("素材使用情况") or []
    checks = data.get("checks") or data.get("需人工核验信息") or []

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{
      --text: #1f2937;
      --muted: #64748b;
      --line: #d8dee8;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --accent: #1d4ed8;
      --accent-soft: #e8f0ff;
      --warn: #8a5a00;
      --warn-bg: #fff7df;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--text);
      background: var(--bg);
      line-height: 1.65;
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 40px 28px 64px; }}
    header {{ margin-bottom: 28px; }}
    h1 {{ font-size: 30px; line-height: 1.3; margin: 0 0 12px; }}
    h2 {{ font-size: 20px; margin: 0 0 14px; }}
    h3 {{ font-size: 17px; margin: 10px 0 12px; }}
    .meta {{ color: var(--muted); font-size: 14px; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 22px;
      margin: 18px 0;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }}
    .lead {{ color: #334155; margin: 0; }}
    .kb-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .kb-link {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      min-height: 56px;
      padding: 14px 16px;
      border-radius: 8px;
      border: 1px solid #bfd0ff;
      background: var(--accent-soft);
      color: var(--accent);
      text-decoration: none;
      font-weight: 650;
    }}
    .kb-link small {{ color: #315fb8; white-space: nowrap; font-weight: 500; }}
    .material-group {{ margin-top: 22px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
    .material-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px;
    }}
    .card-top {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 999px;
      background: #eef2f7;
      color: #334155;
      font-size: 13px;
    }}
    .index {{ color: var(--muted); font-size: 13px; }}
    dl {{ margin: 0; }}
    dl div {{ border-top: 1px solid #eef2f7; padding: 10px 0; }}
    dt {{ color: var(--muted); font-size: 13px; margin-bottom: 2px; }}
    dd {{ margin: 0; }}
    .verify {{
      margin-top: 10px;
      padding: 10px 12px;
      border-radius: 8px;
      color: var(--warn);
      background: var(--warn-bg);
    }}
    ol {{ margin: 0; padding-left: 24px; }}
    .empty {{ color: var(--muted); margin: 0; }}
    footer {{ color: var(--muted); margin-top: 30px; font-size: 13px; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{esc(title)}</h1>
    <div class="meta">生成时间：{esc(generated_at)} ｜ 辅助溯源文件，不是正式正文附件</div>
  </header>

  <section class="panel">
    <h2>可信溯源说明</h2>
    <p class="lead">{esc(summary)}</p>
  </section>

  <section class="panel">
    <h2>知识专库链接</h2>
    {render_kb_links(knowledge_bases)}
  </section>

  <section>
    <h2>素材使用情况</h2>
    {render_materials(materials)}
  </section>

  <section class="panel">
    <h2>需人工核验信息</h2>
    {render_checks(checks)}
  </section>

  <footer>【AI生成提示】内容由AI生成，内容仅供参考。</footer>
</main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="生成素材来源说明 HTML")
    parser.add_argument("input", help="结构化素材来源 JSON，必须位于 official-docs/input、output 或 search-results")
    parser.add_argument("--output", "-o", help="输出 HTML 文件名，默认根据标题生成并保存到 official-docs/output")
    args = parser.parse_args()

    input_path = resolve_input_json(args.input)
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title") or data.get("标题") or input_path.stem
    output_path = resolve_output_html(args.output, title)
    output_path.write_text(render_html(data), encoding="utf-8")
    print(f"✓ 素材来源说明 HTML 已生成: {output_path.relative_to(SKILL_ROOT)}")


if __name__ == "__main__":
    main()
