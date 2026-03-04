"""Filter bar widget for the list screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, SelectionList


class MultiSelectDialog(ModalScreen[list[str] | None]):
    """Modal with a SelectionList for multi-selection."""

    DEFAULT_CSS = """
    MultiSelectDialog {
        align: center middle;
    }
    #ms-dialog-box {
        width: 50;
        height: auto;
        max-height: 24;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #ms-dialog-box SelectionList {
        height: auto;
        max-height: 16;
        margin-bottom: 1;
    }
    #ms-buttons {
        layout: horizontal;
        height: 3;
        align: right middle;
    }
    #ms-buttons Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        title: str,
        options: list[str],
        selected: list[str],
    ) -> None:
        super().__init__()
        self._title = title
        self._options = options
        self._selected = set(selected)

    def compose(self) -> ComposeResult:
        items = [
            (label, label, label in self._selected)
            for label in self._options
        ]
        with Vertical(id="ms-dialog-box"):
            yield SelectionList[str](*items, id="ms-list")
            with Horizontal(id="ms-buttons"):
                yield Button("All", id="btn-all")
                yield Button("None", id="btn-none")
                yield Button("OK", variant="primary", id="btn-ok")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            sel = self.query_one("#ms-list", SelectionList)
            self.dismiss(list(sel.selected))
        elif event.button.id == "btn-all":
            sel = self.query_one("#ms-list", SelectionList)
            sel.select_all()
        elif event.button.id == "btn-none":
            sel = self.query_one("#ms-list", SelectionList)
            sel.deselect_all()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class FilterBar(Horizontal):
    """Top filter bar with multi-select type, state, iteration buttons and search."""

    DEFAULT_CSS = """
    FilterBar {
        height: 3;
        dock: top;
        padding: 0 1;
        background: $surface;
    }
    FilterBar Button {
        width: 1fr;
        margin-right: 1;
    }
    FilterBar Input {
        width: 1fr;
    }
    """

    class FiltersChanged(Message):
        """Posted when any filter value changes."""

        def __init__(
            self,
            work_item_types: list[str],
            states: list[str],
            iterations: list[str],
            search: str,
        ) -> None:
            super().__init__()
            self.work_item_types = work_item_types
            self.states = states
            self.iterations = iterations
            self.search = search

    def __init__(
        self,
        types: list[str] | None = None,
        states: list[str] | None = None,
        iterations: list[str] | None = None,
    ) -> None:
        super().__init__()
        self._types = types or []
        self._states = states or ["New", "Active", "Resolved", "Closed"]
        self._iterations = iterations or []
        # Selected values (empty = all)
        self._sel_types: list[str] = []
        self._sel_states: list[str] = []
        self._sel_iterations: list[str] = []

    def compose(self) -> ComposeResult:
        yield Button("Type: All", id="btn-filter-type")
        yield Button("State: All", id="btn-filter-state")
        yield Button("Iteration: All", id="btn-filter-iteration")
        yield Input(placeholder="Search title...", id="filter-search")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-filter-type":
            self.app.push_screen(
                MultiSelectDialog("Type", self._types, self._sel_types),
                callback=self._on_type_selected,
            )
        elif event.button.id == "btn-filter-state":
            self.app.push_screen(
                MultiSelectDialog("State", self._states, self._sel_states),
                callback=self._on_state_selected,
            )
        elif event.button.id == "btn-filter-iteration":
            self.app.push_screen(
                MultiSelectDialog("Iteration", self._iterations, self._sel_iterations),
                callback=self._on_iteration_selected,
            )

    def _on_type_selected(self, result: list[str] | None) -> None:
        if result is None:
            return
        self._sel_types = result
        btn = self.query_one("#btn-filter-type", Button)
        btn.label = _summary("Type", result, self._types)
        self._post_filters()

    def _on_state_selected(self, result: list[str] | None) -> None:
        if result is None:
            return
        self._sel_states = result
        btn = self.query_one("#btn-filter-state", Button)
        btn.label = _summary("State", result, self._states)
        self._post_filters()

    def _on_iteration_selected(self, result: list[str] | None) -> None:
        if result is None:
            return
        self._sel_iterations = result
        btn = self.query_one("#btn-filter-iteration", Button)
        btn.label = _summary("Iteration", result, self._iterations)
        self._post_filters()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter-search":
            self._post_filters()

    def _post_filters(self) -> None:
        search_input = self.query_one("#filter-search", Input)
        self.post_message(
            self.FiltersChanged(
                work_item_types=self._sel_types,
                states=self._sel_states,
                iterations=self._sel_iterations,
                search=search_input.value,
            )
        )

    def update_iterations(self, iterations: list[str]) -> None:
        """Update the available iteration options."""
        self._iterations = iterations


def _summary(prefix: str, selected: list[str], all_options: list[str]) -> str:
    """Build a button label like 'Type: Bug, Task' or 'Type: All'."""
    if not selected or len(selected) == len(all_options):
        return f"{prefix}: All"
    if len(selected) == 1:
        return f"{prefix}: {selected[0]}"
    if len(selected) == 2:
        return f"{prefix}: {selected[0]}, {selected[1]}"
    return f"{prefix}: {selected[0]} +{len(selected) - 1}"
