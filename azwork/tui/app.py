"""Main Textual application."""

from __future__ import annotations

from textual.app import App

from azwork.api.client import AzureDevOpsClient
from azwork.config import Config
from azwork.tui.screens.list_screen import ListScreen


class AzworkApp(App):
    """Azure DevOps Work Items TUI."""

    TITLE = "azwork"

    CSS = """
    Screen {
        background: $background;
    }
    """

    def __init__(self, config: Config, client: AzureDevOpsClient | None = None) -> None:
        super().__init__()
        self.config = config
        self.client = client or AzureDevOpsClient(
            org=config.org,
            project=config.project,
            pat=config.pat,
        )

    def on_mount(self) -> None:
        self.push_screen(ListScreen(self.config, self.client))
