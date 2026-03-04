"""WIQL query builder for Azure DevOps."""

from __future__ import annotations


def build_wiql(
    project: str,
    work_item_types: list[str] | None = None,
    states: list[str] | None = None,
    iteration_path: str | None = None,
    area_path: str | None = None,
    assigned_to: str | None = None,
    title_contains: str | None = None,
    order_by: str = "System.ChangedDate",
    order_dir: str = "DESC",
) -> str:
    """Build a WIQL query string with optional filters."""
    conditions: list[str] = [
        f"[System.TeamProject] = '{_escape(project)}'"
    ]

    if work_item_types:
        type_list = ", ".join(f"'{_escape(t)}'" for t in work_item_types)
        conditions.append(f"[System.WorkItemType] IN ({type_list})")

    if states:
        state_list = ", ".join(f"'{_escape(s)}'" for s in states)
        conditions.append(f"[System.State] IN ({state_list})")

    if iteration_path:
        conditions.append(
            f"[System.IterationPath] UNDER '{_escape(iteration_path)}'"
        )

    if area_path:
        conditions.append(
            f"[System.AreaPath] UNDER '{_escape(area_path)}'"
        )

    if assigned_to:
        conditions.append(
            f"[System.AssignedTo] = '{_escape(assigned_to)}'"
        )

    if title_contains:
        conditions.append(
            f"[System.Title] CONTAINS '{_escape(title_contains)}'"
        )

    where_clause = " AND ".join(conditions)
    query = (
        f"SELECT [System.Id] FROM WorkItems "
        f"WHERE {where_clause} "
        f"ORDER BY [{order_by}] {order_dir}"
    )
    return query


def _escape(value: str) -> str:
    """Escape single quotes in WIQL values."""
    return value.replace("'", "''")
