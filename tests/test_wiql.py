"""Tests for WIQL query builder."""

from azwork.api.wiql import build_wiql


def test_basic_query():
    q = build_wiql(project="MyProject")
    assert "[System.TeamProject] = 'MyProject'" in q
    assert "SELECT [System.Id] FROM WorkItems" in q
    assert "ORDER BY" in q


def test_with_types():
    q = build_wiql(project="Proj", work_item_types=["Bug", "Task"])
    assert "[System.WorkItemType] IN ('Bug', 'Task')" in q


def test_with_states():
    q = build_wiql(project="Proj", states=["Active", "New"])
    assert "[System.State] IN ('Active', 'New')" in q


def test_with_iteration():
    q = build_wiql(project="Proj", iteration_path="Proj\\Sprint 1")
    assert "[System.IterationPath] UNDER 'Proj\\Sprint 1'" in q


def test_with_area():
    q = build_wiql(project="Proj", area_path="Proj\\Backend")
    assert "[System.AreaPath] UNDER 'Proj\\Backend'" in q


def test_with_assigned_to():
    q = build_wiql(project="Proj", assigned_to="marco@example.com")
    assert "[System.AssignedTo] = 'marco@example.com'" in q


def test_with_title_search():
    q = build_wiql(project="Proj", title_contains="login")
    assert "[System.Title] CONTAINS 'login'" in q


def test_combined_filters():
    q = build_wiql(
        project="Proj",
        work_item_types=["Bug"],
        states=["Active"],
        title_contains="error",
    )
    assert "AND" in q
    assert "'Bug'" in q
    assert "'Active'" in q
    assert "'error'" in q


def test_escape_single_quotes():
    q = build_wiql(project="My'Project")
    assert "My''Project" in q


def test_custom_order():
    q = build_wiql(project="Proj", order_by="System.Id", order_dir="ASC")
    assert "ORDER BY [System.Id] ASC" in q
