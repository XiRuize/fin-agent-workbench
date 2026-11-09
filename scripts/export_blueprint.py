#!/usr/bin/env python3
"""Export a DSH blueprint JSON into a portable payload and a Markdown summary.

Usage:
    python scripts/export_blueprint.py <blueprint.json> <out-dir>

The saved `.dsh/blueprints/<session>.json` contains session metadata; this
script strips it down to the fields accepted by `blueprint(action="create")`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PAYLOAD_KEYS = ("title", "summary", "prompt", "layers", "sections", "diagrams", "modules")


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def mermaid_label(value: object) -> str:
    return str(value).replace('"', "'").replace("\n", " ")


def export_flowchart(diagram: dict) -> list[str]:
    lines = ["```mermaid", "flowchart TD"]
    for node in diagram.get("nodes", []):
        node_id = node["id"]
        label = mermaid_label(node.get("label", node_id))
        node_type = node.get("type", "process")
        if node_type in {"start", "end"}:
            lines.append(f'  {node_id}(["{label}"])')
        elif node_type == "decision":
            lines.append(f'  {node_id}{{"{label}"}}')
        elif node_type == "group":
            continue
        elif node_type == "note":
            lines.append(f'  {node_id}>"{label}"]')
        else:
            lines.append(f'  {node_id}["{label}"]')
    for edge in diagram.get("edges", []):
        label = mermaid_label(edge.get("label", ""))
        arrow = "-->" if label else "-->"
        suffix = f"|{label}|" if label else ""
        lines.append(f"  {edge['from']} {arrow}{suffix} {edge['to']}")
    lines.append("```")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("blueprint")
    parser.add_argument("out_dir")
    args = parser.parse_args()

    source = Path(args.blueprint)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(source.read_text(encoding="utf-8"))
    payload = {key: data[key] for key in PAYLOAD_KEYS if key in data}

    json_path = out_dir / "m1-m2-workbench.json"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines: list[str] = [
        f"# {data.get('title', 'Blueprint')}",
        "",
        data.get("summary", ""),
        "",
        "> 从当前会话蓝图导出。`m1-m2-workbench.json` 是可被 `blueprint(action=\"create\")` 直接使用的 payload。",
        "",
        "## 层",
        "",
    ]
    for layer in data.get("layers", []):
        parent = layer.get("parentModuleId") or "—"
        lines.append(f"- **{layer['letter']}** {layer['title']}（父模块：`{parent}`）")

    lines += ["", "## 需求", ""]
    for section in data.get("sections", []):
        lines += [f"### {section.get('title', section['key'])}", ""]
        if not section.get("items"):
            lines += ["（空）", ""]
            continue
        lines += ["| 编号 | 条目 | 模块 |", "|---|---|---|"]
        for item in section["items"]:
            lines.append(
                f"| {cell(item.get('code', ''))} | {cell(item.get('text', ''))} | "
                f"{cell(item.get('moduleId') or '—')} |"
            )
        lines.append("")

    lines += ["## 模块", "", "| 编号 | 模块 | id | 层 | 依赖 | 文件 | 验收 |", "|---|---|---|---|---|---|---|"]
    for module in data.get("modules", []):
        depends = ", ".join(f"`{item}`" for item in module.get("dependsOn", [])) or "—"
        files = "<br>".join(cell(item) for item in module.get("files", [])) or "—"
        acceptance = "<br>".join(cell(item) for item in module.get("acceptance", [])) or "—"
        lines.append(
            f"| {cell(module.get('code', ''))} | {cell(module.get('name', ''))} | "
            f"`{cell(module.get('id', ''))}` | {cell(module.get('layerId', ''))} | "
            f"{depends} | {files} | {acceptance} |"
        )

    lines += ["", "## 图解", "", "| 图 | 层 | 节点 | 连线 |", "|---|---|---|---|"]
    for diagram in data.get("diagrams", []):
        if not diagram.get("nodes") and not diagram.get("edges"):
            continue
        lines.append(
            f"| {cell(diagram.get('title', diagram.get('key', '')))} | "
            f"{diagram.get('layerId', '')}:{diagram.get('type', '')} | "
            f"{len(diagram.get('nodes', []))} | {len(diagram.get('edges', []))} |"
        )

    flowcharts = [item for item in data.get("diagrams", []) if item.get("type") == "flowchart"]
    if flowcharts:
        lines += ["", "## 实施计划图", ""]
        lines += export_flowchart(flowcharts[0])
        lines.append("")

    md_path = out_dir / "m1-m2-workbench.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
