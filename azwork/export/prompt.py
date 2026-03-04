"""Claude Code prompt generation from work items."""

from __future__ import annotations

from azwork.api.models import WorkItem
from azwork.export.markdown import work_item_to_markdown


def work_item_to_prompt(
    item: WorkItem,
    assets_prefix: str = "",
) -> tuple[str, list[tuple[str, str]]]:
    """Wrap a work item in a Claude Code ready-to-use prompt.

    Returns ``(prompt_text, images)`` — same image list as
    :func:`work_item_to_markdown`.
    """
    md, images = work_item_to_markdown(item, assets_prefix=assets_prefix)

    prompt = f"""# Task: Resolve the following work item

Analyze the work item described below and take the necessary actions to resolve it.
The project context is described in the CLAUDE.md file at the repository root.

## Work Item

{md}

## Instructions

1. Analyze the work item and identify the affected files
2. Implement the fix or the requested feature
3. Write or update tests to cover the case
4. Verify that existing tests are not broken
5. Briefly describe the changes you made
"""
    return prompt, images
