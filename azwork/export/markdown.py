"""Markdown export for work items."""

from __future__ import annotations

import re
from datetime import datetime

from azwork.api.models import WorkItem
from azwork.utils import ImageCollector, html_to_markdown


def work_item_to_markdown(
    item: WorkItem,
    assets_prefix: str = "",
) -> tuple[str, list[tuple[str, str]]]:
    """Convert a WorkItem to Markdown.

    Returns ``(markdown_text, images)`` where *images* is a list of
    ``(remote_url, local_filename)`` pairs that should be downloaded
    into the assets directory.

    *assets_prefix* is the relative path from the MD file to the assets
    directory (e.g. ``"./1234-assets"``).  When empty, image URLs are
    left unchanged and no images are collected.
    """
    collector = ImageCollector(assets_prefix=assets_prefix) if assets_prefix else None

    lines: list[str] = []

    # Title
    lines.append(f"# [{item.work_item_type}] #{item.id}: {item.title}")
    lines.append("")

    # Metadata table
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| State | {item.state} |")
    if item.priority is not None:
        lines.append(f"| Priority | {item.priority} |")
    if item.severity:
        lines.append(f"| Severity | {item.severity} |")
    if item.area_path:
        lines.append(f"| Area Path | {item.area_path} |")
    if item.iteration_path:
        lines.append(f"| Iteration | {item.iteration_path} |")
    if item.assigned_to:
        lines.append(f"| Assigned To | {item.assigned_to} |")
    if item.created_date:
        lines.append(f"| Created | {item.created_date} |")
    if item.changed_date:
        lines.append(f"| Updated | {item.changed_date} |")
    if item.tags:
        lines.append(f"| Tags | {item.tags} |")
    lines.append("")

    # Description
    if item.description:
        lines.append("## Description")
        lines.append("")
        lines.append(html_to_markdown(item.description, image_collector=collector))
        lines.append("")

    # Repro Steps
    if item.repro_steps:
        lines.append("## Steps to Reproduce")
        lines.append("")
        lines.append(html_to_markdown(item.repro_steps, image_collector=collector))
        lines.append("")

    # Acceptance Criteria
    if item.acceptance_criteria:
        lines.append("## Acceptance Criteria")
        lines.append("")
        lines.append(html_to_markdown(item.acceptance_criteria, image_collector=collector))
        lines.append("")

    # Comments / Discussion
    if item.comments:
        lines.append("## Discussion")
        lines.append("")
        for comment in item.comments:
            date = comment.created_date
            if date and "T" in date:
                try:
                    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
            lines.append(f"### {comment.author} — {date}")
            lines.append("")
            lines.append(html_to_markdown(comment.text, image_collector=collector))
            lines.append("")

    # Relations
    if item.relations:
        lines.append("## Related Work Items")
        lines.append("")
        for rel in item.relations:
            if rel.target_id:
                title_part = f" — {rel.title}" if rel.title else ""
                lines.append(f"- {rel.rel_type}: #{rel.target_id}{title_part}")
            else:
                lines.append(f"- {rel.rel_type}: {rel.url}")
        lines.append("")

    # Custom Fields
    if item.custom_fields:
        lines.append("## Custom Fields")
        lines.append("")
        for key, value in item.custom_fields.items():
            display_name = key.rsplit(".", 1)[-1] if "." in key else key
            display_name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", display_name)
            lines.append(f"- **{display_name}:** {value}")
        lines.append("")

    # Footer
    lines.append("---")
    today = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"*Exported from Azure DevOps on {today} by azwork*")

    images = collector.images if collector else []
    return "\n".join(lines), images
