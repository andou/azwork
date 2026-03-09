"""Tests for Markdown export."""

from azwork.api.models import Comment, Relation, WorkItem
from azwork.export.markdown import work_item_to_markdown
from azwork.export.prompt import work_item_to_prompt


def _make_item(**overrides) -> WorkItem:
    defaults = dict(
        id=1234,
        title="Login fails with special chars",
        work_item_type="Bug",
        state="Active",
        area_path="MyProject\\Backend\\Auth",
        iteration_path="Sprint 24.3",
        assigned_to="Marco Rossi",
        created_date="2025-02-14",
        changed_date="2025-02-16",
        tags="auth, security",
        priority=1,
        severity="2 - High",
        description="<p>Description text</p>",
        repro_steps="<ol><li>Step one</li><li>Step two</li></ol>",
        acceptance_criteria="<p>Must work</p>",
    )
    defaults.update(overrides)
    return WorkItem(**defaults)


class TestWorkItemToMarkdown:
    def test_title(self):
        md, _ = work_item_to_markdown(_make_item())
        assert "# [Bug] #1234: Login fails with special chars" in md

    def test_metadata_table(self):
        md, _ = work_item_to_markdown(_make_item())
        assert "| State | Active |" in md
        assert "| Priority | 1 |" in md
        assert "| Severity | 2 - High |" in md
        assert "| Assigned To | Marco Rossi |" in md

    def test_description_converted(self):
        md, _ = work_item_to_markdown(_make_item())
        assert "## Description" in md
        assert "Description text" in md

    def test_repro_steps(self):
        md, _ = work_item_to_markdown(_make_item())
        assert "## Steps to Reproduce" in md
        assert "Step one" in md

    def test_acceptance_criteria(self):
        md, _ = work_item_to_markdown(_make_item())
        assert "## Acceptance Criteria" in md
        assert "Must work" in md

    def test_no_description(self):
        md, _ = work_item_to_markdown(_make_item(description=""))
        assert "## Description" not in md

    def test_no_repro_steps(self):
        md, _ = work_item_to_markdown(_make_item(repro_steps=""))
        assert "## Steps to Reproduce" not in md

    def test_no_priority(self):
        md, _ = work_item_to_markdown(_make_item(priority=None))
        assert "Priority" not in md

    def test_comments(self):
        item = _make_item()
        item.comments = [
            Comment(id=1, text="<p>First comment</p>", author="Alice", created_date="2025-02-15T10:00:00Z"),
            Comment(id=2, text="<p>Second comment</p>", author="Bob", created_date="2025-02-16T11:00:00Z"),
        ]
        md, _ = work_item_to_markdown(item)
        assert "## Discussion" in md
        assert "### Alice" in md
        assert "First comment" in md
        assert "### Bob" in md

    def test_relations(self):
        item = _make_item()
        item.relations = [
            Relation(rel_type="Parent", url="https://example.com/1200", target_id=1200, title="Parent story"),
        ]
        md, _ = work_item_to_markdown(item)
        assert "## Related Work Items" in md
        assert "#1200" in md

    def test_custom_fields(self):
        item = _make_item()
        item.custom_fields = {"Custom.RootCause": "Input Sanitization"}
        md, _ = work_item_to_markdown(item)
        assert "## Custom Fields" in md
        assert "Input Sanitization" in md

    def test_footer(self):
        md, _ = work_item_to_markdown(_make_item())
        assert "Exported from Azure DevOps" in md
        assert "azwork" in md

    def test_no_images_without_prefix(self):
        item = _make_item(description='<p><img src="https://dev.azure.com/img.png" alt="screenshot"></p>')
        md, images = work_item_to_markdown(item)
        assert images == []
        assert "https://dev.azure.com/img.png" in md

    def test_images_collected_with_prefix(self):
        item = _make_item(
            description='<p><img src="https://dev.azure.com/org/_apis/wit/attachments/abc" alt="screenshot"></p>',
        )
        md, images = work_item_to_markdown(item, assets_prefix="./1234-assets")
        assert len(images) == 1
        assert images[0][0] == "https://dev.azure.com/org/_apis/wit/attachments/abc"
        assert "./1234-assets/" in md
        assert "https://dev.azure.com" not in md

    def test_multiple_images_sequential_names(self):
        item = _make_item(
            description=(
                '<p><img src="https://example.com/a.png" alt="first">'
                '<img src="https://example.com/b.jpg" alt="second"></p>'
            ),
        )
        md, images = work_item_to_markdown(item, assets_prefix="./assets")
        assert len(images) == 2
        assert images[0][1] == "image-1.png"
        assert images[1][1] == "image-2.jpg"

    def test_images_in_comments(self):
        item = _make_item(description="")
        item.comments = [
            Comment(
                id=1,
                text='<p><img src="https://dev.azure.com/img.png" alt="ss"></p>',
                author="Alice",
                created_date="2025-02-15",
            ),
        ]
        md, images = work_item_to_markdown(item, assets_prefix="./1234-assets")
        assert len(images) == 1
        assert "./1234-assets/image-1.png" in md


class TestWorkItemToPrompt:
    def test_contains_work_item(self):
        prompt, _ = work_item_to_prompt(_make_item())
        assert "# Task: Resolve the following work item" in prompt
        assert "# [Bug] #1234" in prompt

    def test_contains_instructions(self):
        prompt, _ = work_item_to_prompt(_make_item())
        assert "## Instructions" in prompt
        assert "Analyze the work item" in prompt
        assert "CLAUDE.md" in prompt

    def test_prompt_collects_images(self):
        item = _make_item(
            description='<p><img src="https://example.com/shot.png" alt="ss"></p>',
        )
        prompt, images = work_item_to_prompt(item, assets_prefix="./1234-assets")
        assert len(images) == 1
        assert "./1234-assets/" in prompt

    def test_custom_prompt_template(self):
        template = "## Custom\n\n{work_item}\n\n## Done"
        prompt, _ = work_item_to_prompt(_make_item(), prompt_template=template)
        assert prompt.startswith("## Custom")
        assert "## Done" in prompt
        assert "# [Bug] #1234" in prompt
        assert "# Task: Resolve" not in prompt

    def test_empty_template_uses_default(self):
        prompt, _ = work_item_to_prompt(_make_item(), prompt_template="")
        assert "# Task: Resolve the following work item" in prompt
