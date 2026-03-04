"""Work item table widget."""

from __future__ import annotations

from textual.message import Message
from textual.widgets import DataTable

from azwork.api.models import WorkItem


class ItemTable(DataTable):
    """DataTable specialised for work items."""

    DEFAULT_CSS = """
    ItemTable {
        height: 1fr;
    }
    """

    class ItemSelected(Message):
        """User selected a work item."""

        def __init__(self, work_item: WorkItem) -> None:
            super().__init__()
            self.work_item = work_item

    class ItemExport(Message):
        """User wants to export a work item."""

        def __init__(self, work_item: WorkItem) -> None:
            super().__init__()
            self.work_item = work_item

    def __init__(self) -> None:
        super().__init__(cursor_type="row")
        self._items: list[WorkItem] = []
        self._sort_key: str = "id"
        self._sort_reverse: bool = True

    def on_mount(self) -> None:
        self.add_columns("ID", "Type", "Title", "State", "Pri.", "Assigned To")

    def load_items(self, items: list[WorkItem]) -> None:
        """Load work items into the table."""
        self._items = list(items)
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        self.clear()
        sorted_items = self._sorted_items()
        for item in sorted_items:
            self.add_row(
                str(item.id),
                item.work_item_type,
                item.title[:80],
                item.state,
                str(item.priority or ""),
                item.assigned_to[:25] if item.assigned_to else "",
                key=str(item.id),
            )

    def _sorted_items(self) -> list[WorkItem]:
        key_map = {
            "id": lambda x: x.id,
            "type": lambda x: x.work_item_type,
            "title": lambda x: x.title.lower(),
            "state": lambda x: x.state,
            "priority": lambda x: x.priority or 999,
            "assigned": lambda x: x.assigned_to.lower(),
        }
        key_fn = key_map.get(self._sort_key, key_map["id"])
        return sorted(self._items, key=key_fn, reverse=self._sort_reverse)

    def sort_by(self, column: str) -> None:
        if self._sort_key == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_key = column
            self._sort_reverse = False
        self._refresh_rows()

    def get_selected_item(self) -> WorkItem | None:
        if self.cursor_row is not None and self.cursor_row < len(self._items):
            row_key = self._get_row_key_at_cursor()
            if row_key:
                for item in self._items:
                    if str(item.id) == str(row_key):
                        return item
        return None

    def _get_row_key_at_cursor(self) -> str | None:
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            return str(row_key.value)
        except Exception:
            return None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = str(event.row_key.value)
        for item in self._items:
            if str(item.id) == key:
                self.post_message(self.ItemSelected(item))
                break

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        col_map = {0: "id", 1: "type", 2: "title", 3: "state", 4: "priority", 5: "assigned"}
        col_idx = event.column_index
        if col_idx in col_map:
            self.sort_by(col_map[col_idx])
