"""Work item list screen."""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from azwork.api.client import AzureDevOpsClient, AzureDevOpsError
from azwork.api.models import WorkItem
from azwork.api.wiql import build_wiql
from azwork.config import Config
from azwork.tui.widgets.filter_bar import FilterBar
from azwork.tui.widgets.item_table import ItemTable


class ListScreen(Screen):
    """Main list screen showing work items."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("e", "export", "Export MD"),
        Binding("question_mark", "help", "Help"),
    ]

    DEFAULT_CSS = """
    ListScreen {
        layout: vertical;
    }
    #status-bar {
        height: 1;
        dock: bottom;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, config: Config, client: AzureDevOpsClient) -> None:
        super().__init__()
        self.config = config
        self.client = client
        self._all_items: list[WorkItem] = []
        self._iterations: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield FilterBar(
            types=self.config.work_item_types,
            iterations=[],
        )
        yield Vertical(
            ItemTable(),
            id="table-container",
        )
        yield Static("Loading work items...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"azwork — {self.config.org} / {self.config.project}"
        self._load_data()

    @work(thread=True)
    def _load_data(self) -> None:
        """Load work items and iterations from the API."""
        status = self.query_one("#status-bar", Static)
        table = self.query_one(ItemTable)

        try:
            # Load iterations in the background
            try:
                iterations = self.client.get_iterations()
                self._iterations = iterations
                filter_bar = self.query_one(FilterBar)
                self.app.call_from_thread(filter_bar.update_iterations, iterations)
            except AzureDevOpsError:
                pass

            # Build and execute query
            wiql = build_wiql(
                project=self.config.project,
                work_item_types=self.config.work_item_types,
            )
            self.app.call_from_thread(status.update, "Querying work items...")
            ids = self.client.query_work_item_ids(wiql)

            if not ids:
                self.app.call_from_thread(status.update, "No work items found.")
                return

            # Fetch details in batches
            def on_progress(batch: int, total: int) -> None:
                self.app.call_from_thread(
                    status.update,
                    f"Loading work items... batch {batch}/{total}",
                )

            items = self.client.get_work_items(ids, progress_callback=on_progress)
            self._all_items = items

            self.app.call_from_thread(table.load_items, items)
            self.app.call_from_thread(
                status.update,
                f"Work Items: {len(items)}  |  ↑↓ Navigate  Enter: Detail  E: Export  R: Refresh  Q: Quit  ?: Help",
            )

        except AzureDevOpsError as e:
            self.app.call_from_thread(status.update, f"Error: {e}")

    def on_filter_bar_filters_changed(self, event: FilterBar.FiltersChanged) -> None:
        """Apply filters to the work item list."""
        filtered = self._all_items

        if event.work_item_types:
            allowed = set(event.work_item_types)
            filtered = [i for i in filtered if i.work_item_type in allowed]

        if event.states:
            allowed = set(event.states)
            filtered = [i for i in filtered if i.state in allowed]

        if event.iterations:
            allowed = set(event.iterations)
            filtered = [i for i in filtered if i.iteration_path in allowed]

        if event.search:
            search_lower = event.search.lower()
            filtered = [i for i in filtered if search_lower in i.title.lower()]

        table = self.query_one(ItemTable)
        table.load_items(filtered)

        status = self.query_one("#status-bar", Static)
        status.update(
            f"Work Items: {len(filtered)} (of {len(self._all_items)})  |  "
            "↑↓ Navigate  Enter: Detail  E: Export  R: Refresh  Q: Quit  ?: Help"
        )

    def on_item_table_item_selected(self, event: ItemTable.ItemSelected) -> None:
        """Open the detail screen for the selected item."""
        from azwork.tui.screens.detail_screen import DetailScreen

        self.app.push_screen(DetailScreen(event.work_item, self.config, self.client))

    def action_refresh(self) -> None:
        """Refresh work items from API."""
        self.client.clear_cache()
        self._all_items.clear()
        table = self.query_one(ItemTable)
        table.clear()
        status = self.query_one("#status-bar", Static)
        status.update("Refreshing...")
        self._load_data()

    def action_export(self) -> None:
        """Export the currently highlighted work item."""
        table = self.query_one(ItemTable)
        item = table.get_selected_item()
        if item:
            from azwork.tui.screens.detail_screen import ExportDialog

            self.app.push_screen(ExportDialog(item, self.config, self.client, mode="markdown"))

    def action_help(self) -> None:
        self.notify(
            "↑↓: Navigate | Enter: Detail | E: Export | R: Refresh | Q: Quit",
            title="Help",
        )

    def action_quit(self) -> None:
        self.app.exit()
