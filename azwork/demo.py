"""Demo mode with fake data for recordings and screenshots."""

from __future__ import annotations

from azwork.api.models import Comment, Relation, WorkItem


DEMO_ITEMS = [
    WorkItem(
        id=1042,
        title="Login page crashes on invalid email format",
        work_item_type="Bug",
        state="Active",
        area_path="Acme\\Backend",
        iteration_path="Acme\\Sprint 14",
        assigned_to="Alice Martin",
        created_date="2026-02-28",
        changed_date="2026-03-10",
        tags="regression; auth",
        priority=1,
        severity="2 - High",
        description="<p>When a user enters an email without '@', the login page throws an unhandled exception and shows a blank screen.</p>",
        repro_steps="<ol><li>Go to /login</li><li>Enter 'testuser' in email field</li><li>Click Sign In</li><li>Observe blank screen</li></ol>",
        acceptance_criteria="<p>Invalid emails show a validation message. No crash.</p>",
    ),
    WorkItem(
        id=1038,
        title="Add dark mode support to settings panel",
        work_item_type="User Story",
        state="New",
        area_path="Acme\\Frontend",
        iteration_path="Acme\\Sprint 14",
        assigned_to="Bob Chen",
        created_date="2026-02-25",
        changed_date="2026-03-08",
        tags="ui; accessibility",
        priority=2,
        severity="",
        description="<p>As a user, I want to toggle dark mode from the settings panel so that I can reduce eye strain.</p>",
        acceptance_criteria="<ul><li>Toggle switch in settings</li><li>Theme persists across sessions</li><li>Respects OS preference by default</li></ul>",
    ),
    WorkItem(
        id=1035,
        title="API rate limiter returns 500 instead of 429",
        work_item_type="Bug",
        state="Active",
        area_path="Acme\\Backend",
        iteration_path="Acme\\Sprint 13",
        assigned_to="Alice Martin",
        created_date="2026-02-20",
        changed_date="2026-03-09",
        tags="api; reliability",
        priority=1,
        severity="1 - Critical",
        description="<p>The rate limiter middleware throws an internal server error (500) when the request limit is exceeded, instead of returning a proper 429 Too Many Requests response.</p>",
        repro_steps="<ol><li>Send 100+ requests/sec to any endpoint</li><li>Observe 500 responses after threshold</li></ol>",
        acceptance_criteria="<p>Returns 429 with Retry-After header when rate limit is exceeded.</p>",
    ),
    WorkItem(
        id=1029,
        title="Implement CSV export for reports",
        work_item_type="Task",
        state="Active",
        area_path="Acme\\Backend",
        iteration_path="Acme\\Sprint 14",
        assigned_to="Carol Davis",
        created_date="2026-02-15",
        changed_date="2026-03-07",
        tags="export; reporting",
        priority=2,
        severity="",
        description="<p>Add CSV export option to the reports page. Should support all report types and respect current filters.</p>",
    ),
    WorkItem(
        id=1024,
        title="Search index out of sync after bulk delete",
        work_item_type="Bug",
        state="Resolved",
        area_path="Acme\\Search",
        iteration_path="Acme\\Sprint 13",
        assigned_to="Dave Wilson",
        created_date="2026-02-10",
        changed_date="2026-03-05",
        tags="search; data-integrity",
        priority=2,
        severity="2 - High",
        description="<p>After performing a bulk delete of documents, the search index still returns deleted items for up to 30 minutes.</p>",
    ),
    WorkItem(
        id=1019,
        title="Upgrade authentication to OAuth 2.0 PKCE flow",
        work_item_type="User Story",
        state="New",
        area_path="Acme\\Security",
        iteration_path="Acme\\Sprint 15",
        assigned_to="Eve Thompson",
        created_date="2026-02-05",
        changed_date="2026-03-01",
        tags="security; auth",
        priority=1,
        severity="",
        description="<p>Migrate from implicit OAuth flow to PKCE to improve security for public clients.</p>",
        acceptance_criteria="<ul><li>PKCE flow implemented</li><li>Backward-compatible token refresh</li><li>All existing sessions remain valid</li></ul>",
    ),
    WorkItem(
        id=1015,
        title="Dashboard widgets fail to load on slow connections",
        work_item_type="Bug",
        state="Active",
        area_path="Acme\\Frontend",
        iteration_path="Acme\\Sprint 14",
        assigned_to="Bob Chen",
        created_date="2026-01-30",
        changed_date="2026-03-06",
        tags="performance; dashboard",
        priority=3,
        severity="3 - Medium",
        description="<p>Dashboard widgets show a permanent spinner when network latency exceeds 3 seconds. No timeout or retry mechanism.</p>",
    ),
    WorkItem(
        id=1010,
        title="Set up CI/CD pipeline for staging environment",
        work_item_type="Task",
        state="Closed",
        area_path="Acme\\DevOps",
        iteration_path="Acme\\Sprint 12",
        assigned_to="Frank Garcia",
        created_date="2026-01-20",
        changed_date="2026-02-28",
        tags="devops; ci-cd",
        priority=2,
        severity="",
        description="<p>Configure GitHub Actions pipeline for automated deployments to the staging environment on merge to develop branch.</p>",
    ),
]

DEMO_COMMENTS = {
    1042: [
        Comment(id=1, text="<p>Reproduced on Chrome 120 and Firefox 121. Stack trace points to EmailValidator.validate().</p>", author="Alice Martin", created_date="2026-03-01"),
        Comment(id=2, text="<p>This might be related to the regex update in PR #287. Checking now.</p>", author="Bob Chen", created_date="2026-03-02"),
    ],
    1035: [
        Comment(id=3, text="<p>Root cause: the rate limiter catches the exception but re-raises it as a generic error. Fix in PR #301.</p>", author="Alice Martin", created_date="2026-03-09"),
    ],
    1024: [
        Comment(id=4, text="<p>Fixed by adding synchronous index invalidation on bulk operations. Verified in staging.</p>", author="Dave Wilson", created_date="2026-03-04"),
    ],
}

DEMO_ITERATIONS = [
    "Acme\\Sprint 12",
    "Acme\\Sprint 13",
    "Acme\\Sprint 14",
    "Acme\\Sprint 15",
]


class DemoClient:
    """A fake client that returns demo data without any network calls."""

    def __init__(self) -> None:
        self.org = "acme-org"
        self.project = "Acme"
        self._cache: dict[int, WorkItem] = {item.id: item for item in DEMO_ITEMS}

    def query_work_item_ids(self, wiql: str) -> list[int]:
        return [item.id for item in DEMO_ITEMS]

    def get_work_items(
        self,
        ids: list[int],
        progress_callback=None,
    ) -> list[WorkItem]:
        if progress_callback:
            progress_callback(1, 1)
        return [self._cache[wid] for wid in ids if wid in self._cache]

    def get_comments(self, work_item_id: int) -> list[Comment]:
        return DEMO_COMMENTS.get(work_item_id, [])

    def get_iterations(self) -> list[str]:
        return DEMO_ITERATIONS

    def get_fields(self) -> list[dict]:
        return []

    def get_work_item_url(self, work_item_id: int) -> str:
        return f"https://dev.azure.com/{self.org}/{self.project}/_workitems/edit/{work_item_id}"

    def download_image(self, url: str) -> bytes:
        return b""

    def clear_cache(self) -> None:
        self._cache = {item.id: item for item in DEMO_ITEMS}
