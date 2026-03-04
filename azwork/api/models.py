"""Data models for Azure DevOps work items."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Comment:
    id: int
    text: str
    author: str
    created_date: str

    @classmethod
    def from_api(cls, data: dict) -> Comment:
        author = data.get("createdBy", {}).get("displayName", "Unknown")
        return cls(
            id=data.get("id", 0),
            text=data.get("text", ""),
            author=author,
            created_date=data.get("createdDate", ""),
        )


@dataclass
class Relation:
    rel_type: str
    url: str
    target_id: int | None = None
    title: str | None = None

    @classmethod
    def from_api(cls, data: dict) -> Relation:
        url = data.get("url", "")
        # Extract work item ID from URL
        target_id = None
        if "/workItems/" in url:
            try:
                target_id = int(url.rsplit("/", 1)[-1])
            except ValueError:
                pass
        attributes = data.get("attributes", {})
        return cls(
            rel_type=attributes.get("name", data.get("rel", "")),
            url=url,
            target_id=target_id,
            title=None,
        )


@dataclass
class WorkItem:
    id: int
    title: str = ""
    work_item_type: str = ""
    state: str = ""
    area_path: str = ""
    iteration_path: str = ""
    assigned_to: str = ""
    created_date: str = ""
    changed_date: str = ""
    tags: str = ""
    priority: int | None = None
    severity: str = ""
    description: str = ""
    repro_steps: str = ""
    acceptance_criteria: str = ""
    custom_fields: dict[str, str] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    url: str = ""

    # Standard field reference names
    STANDARD_FIELDS: set[str] = field(
        default_factory=lambda: {
            "System.Id",
            "System.Title",
            "System.Description",
            "System.State",
            "System.WorkItemType",
            "System.AreaPath",
            "System.IterationPath",
            "System.AssignedTo",
            "System.CreatedDate",
            "System.ChangedDate",
            "System.Tags",
            "System.Reason",
            "System.Rev",
            "System.TeamProject",
            "System.BoardColumn",
            "System.BoardColumnDone",
            "System.CommentCount",
            "System.History",
            "System.Watermark",
            "System.AuthorizedAs",
            "System.NodeName",
            "System.RelatedLinkCount",
            "System.ExternalLinkCount",
            "System.HyperLinkCount",
            "System.AttachedFileCount",
            "System.AuthorizedDate",
            "System.RevisedDate",
            "System.PersonId",
            "System.CreatedBy",
            "System.ChangedBy",
            "Microsoft.VSTS.Common.Priority",
            "Microsoft.VSTS.Common.Severity",
            "Microsoft.VSTS.Common.StateChangeDate",
            "Microsoft.VSTS.Common.ActivatedDate",
            "Microsoft.VSTS.Common.ActivatedBy",
            "Microsoft.VSTS.Common.ResolvedDate",
            "Microsoft.VSTS.Common.ResolvedBy",
            "Microsoft.VSTS.Common.ResolvedReason",
            "Microsoft.VSTS.Common.ClosedDate",
            "Microsoft.VSTS.Common.ClosedBy",
            "Microsoft.VSTS.Common.ValueArea",
            "Microsoft.VSTS.Common.StackRank",
            "Microsoft.VSTS.TCM.ReproSteps",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "Microsoft.VSTS.Scheduling.StoryPoints",
            "Microsoft.VSTS.Scheduling.Effort",
            "Microsoft.VSTS.Scheduling.RemainingWork",
            "Microsoft.VSTS.Scheduling.OriginalEstimate",
            "Microsoft.VSTS.Scheduling.CompletedWork",
            "WEF_",
        },
        repr=False,
    )

    @classmethod
    def from_api(cls, data: dict) -> WorkItem:
        fields = data.get("fields", {})
        assigned_to = fields.get("System.AssignedTo", {})
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get("displayName", "")

        item = cls(
            id=data.get("id", fields.get("System.Id", 0)),
            title=fields.get("System.Title", ""),
            work_item_type=fields.get("System.WorkItemType", ""),
            state=fields.get("System.State", ""),
            area_path=fields.get("System.AreaPath", ""),
            iteration_path=fields.get("System.IterationPath", ""),
            assigned_to=assigned_to,
            created_date=_format_date(fields.get("System.CreatedDate", "")),
            changed_date=_format_date(fields.get("System.ChangedDate", "")),
            tags=fields.get("System.Tags", ""),
            priority=fields.get("Microsoft.VSTS.Common.Priority"),
            severity=fields.get("Microsoft.VSTS.Common.Severity", ""),
            description=fields.get("System.Description", "") or "",
            repro_steps=fields.get("Microsoft.VSTS.TCM.ReproSteps", "") or "",
            acceptance_criteria=fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", "") or "",
            url=data.get("_links", {}).get("html", {}).get("href", ""),
        )

        # Extract custom fields
        standard = item.STANDARD_FIELDS
        for key, value in fields.items():
            if value is None or value == "":
                continue
            is_standard = any(key.startswith(prefix) for prefix in ("System.", "Microsoft.VSTS."))
            is_wef = key.startswith("WEF_")
            if not is_standard and not is_wef:
                item.custom_fields[key] = str(value)

        # Extract relations
        for rel_data in data.get("relations", []) or []:
            item.relations.append(Relation.from_api(rel_data))

        return item


def _format_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str
