"""Work item detail screen and export dialog."""

from __future__ import annotations

import logging
import os
import webbrowser
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, Label, Markdown, Static

from azwork.api.client import AzureDevOpsClient, AzureDevOpsError
from azwork.api.models import WorkItem
from azwork.config import Config
from azwork.export.markdown import work_item_to_markdown
from azwork.export.prompt import work_item_to_prompt
from azwork.utils import slugify

log = logging.getLogger(__name__)


class DetailScreen(Screen):
    """Detail view for a single work item."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("e", "export_md", "Export MD"),
        Binding("p", "export_prompt", "Export Prompt"),
        Binding("c", "copy_md", "Copy MD"),
        Binding("o", "open_browser", "Open in Browser"),
        Binding("question_mark", "help", "Help"),
    ]

    DEFAULT_CSS = """
    DetailScreen {
        layout: vertical;
    }
    #detail-content {
        height: 1fr;
        padding: 1 2;
    }
    #detail-status {
        height: 1;
        dock: bottom;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, item: WorkItem, config: Config, client: AzureDevOpsClient) -> None:
        super().__init__()
        self.item = item
        self.config = config
        self.client = client

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Markdown("Loading...", id="detail-md"),
            id="detail-content",
        )
        yield Static(
            "Esc: Back  E: Export MD  P: Export Prompt  C: Copy MD  O: Open  ?: Help",
            id="detail-status",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"{self.item.work_item_type} #{self.item.id}: {self.item.title}"
        self._load_comments()

    @work(thread=True)
    def _load_comments(self) -> None:
        """Fetch comments and render the detail view."""
        try:
            comments = self.client.get_comments(self.item.id)
            self.item.comments = comments
        except AzureDevOpsError:
            pass

        md_text, _images = work_item_to_markdown(self.item)
        md_widget = self.query_one("#detail-md", Markdown)
        self.app.call_from_thread(md_widget.update, md_text)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_export_md(self) -> None:
        self.app.push_screen(ExportDialog(self.item, self.config, self.client, mode="markdown"))

    def action_export_prompt(self) -> None:
        self.app.push_screen(ExportDialog(self.item, self.config, self.client, mode="prompt"))

    def action_copy_md(self) -> None:
        md, _images = work_item_to_markdown(self.item)
        try:
            import pyperclip

            pyperclip.copy(md)
            self.notify("Markdown copied to clipboard!")
        except Exception as e:
            self.notify(f"Copy failed: {e}", severity="error")

    def action_open_browser(self) -> None:
        url = self.client.get_work_item_url(self.item.id)
        webbrowser.open(url)
        self.notify(f"Opened #{self.item.id} in browser")

    def action_help(self) -> None:
        self.notify(
            "Esc: Back | E: Export MD | P: Export Prompt | C: Copy | O: Open in Browser",
            title="Help",
        )


class ExportDialog(ModalScreen[str | None]):
    """Modal dialog for choosing export path."""

    DEFAULT_CSS = """
    ExportDialog {
        align: center middle;
    }
    #export-dialog-box {
        width: 70;
        height: auto;
        max-height: 15;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #export-dialog-box Label {
        margin-bottom: 1;
    }
    #export-dialog-box Input {
        margin-bottom: 1;
    }
    #export-buttons {
        layout: horizontal;
        height: 3;
        align: right middle;
    }
    #export-buttons Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        item: WorkItem,
        config: Config,
        client: AzureDevOpsClient,
        mode: str = "markdown",
    ) -> None:
        super().__init__()
        self.item = item
        self.config = config
        self.client = client
        self.mode = mode

    def compose(self) -> ComposeResult:
        slug = slugify(self.item.title)
        filename = f"{self.item.id}-{slug}.md"
        default_dir = self.config.default_output_dir
        default_path = os.path.join(default_dir, filename)

        label = "Export as Markdown" if self.mode == "markdown" else "Export as Claude Code Prompt"

        with Vertical(id="export-dialog-box"):
            yield Label(label)
            yield Input(value=default_path, id="export-path")
            with Vertical(id="export-buttons"):
                yield Button("Save", variant="primary", id="btn-save")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._do_save()
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_save()

    def _do_save(self) -> None:
        path_input = self.query_one("#export-path", Input)
        file_path = Path(path_input.value).expanduser()

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Assets directory: <id>-assets/ next to the MD file
        assets_dir_name = f"{self.item.id}-assets"
        assets_prefix = f"./{assets_dir_name}"

        # Generate content with image rewriting
        if self.mode == "markdown":
            content, images = work_item_to_markdown(self.item, assets_prefix=assets_prefix)
        else:
            content, images = work_item_to_prompt(
                self.item, assets_prefix=assets_prefix,
                prompt_template=self.config.prompt_template,
            )

        try:
            file_path.write_text(content, encoding="utf-8")

            # Download images
            if images:
                assets_path = file_path.parent / assets_dir_name
                assets_path.mkdir(parents=True, exist_ok=True)
                downloaded = 0
                for remote_url, local_name in images:
                    try:
                        data = self.client.download_image(remote_url)
                        (assets_path / local_name).write_bytes(data)
                        downloaded += 1
                    except AzureDevOpsError as e:
                        log.warning("Failed to download %s: %s", remote_url, e)

                self.app.notify(
                    f"Exported to {file_path} ({downloaded}/{len(images)} images)"
                )
            else:
                self.app.notify(f"Exported to {file_path}")

            self.dismiss(str(file_path))
        except OSError as e:
            self.app.notify(f"Export failed: {e}", severity="error")
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
