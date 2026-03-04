# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is azwork

A Python TUI for triaging Azure DevOps work items. Browse, filter, and inspect work items interactively, then export them as Markdown or as Claude Code prompts. Built with Textual (TUI), requests (API), BeautifulSoup (HTML→MD conversion).

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_wiql.py

# Run a single test by name
pytest tests/test_api_client.py::TestGetWorkItems::test_caches_items -v

# Launch the TUI
azwork

# Run setup wizard
azwork --setup
```

## Architecture

**Config cascade**: `~/.azwork.yml` → `AZURE_DEVOPS_PAT` env var → CLI args (`--org`, `--project`, `--output-dir`). PAT is never persisted to disk.

**Data flow**: `__main__.py` parses CLI → `Config.load()` merges sources → `AzworkApp` creates `AzureDevOpsClient` → `ListScreen` builds WIQL via `build_wiql()` → client fetches IDs then batch-fetches details (200/batch) → items displayed in `ItemTable` → `DetailScreen` fetches comments on open → export pipeline converts `WorkItem` → Markdown (with HTML→MD conversion) or Claude Code prompt.

**TUI screen stack**: `AzworkApp` pushes `ListScreen` on mount. `Enter` pushes `DetailScreen`. `E`/`P` pushes `ExportDialog` (a `ModalScreen` that returns the saved path or `None`). `Esc` pops back.

**API client caching**: `AzureDevOpsClient._cache` is a `dict[int, WorkItem]` populated on fetch. `get_work_items()` only fetches uncached IDs. Cache is cleared explicitly on refresh (`R` key). Comments are not cached — fetched each time the detail screen opens.

**Async pattern**: All blocking API calls run in background threads via Textual's `@work(thread=True)` decorator. UI updates from these threads use `self.app.call_from_thread()`.

## Key conventions

- **Model parsing**: All API models (`WorkItem`, `Comment`, `Relation`) have a `from_api(cls, data: dict)` classmethod that transforms raw JSON into the dataclass.
- **Custom fields**: `WorkItem.from_api()` auto-discovers fields that don't start with `System.`, `Microsoft.VSTS.`, or `WEF_` and puts them in `custom_fields`.
- **Widget communication**: Widgets post custom `Message` subclasses. Parent screens handle them via `on_<widget_class>_<message_class>()` methods (e.g., `on_filter_bar_filters_changed`).
- **WIQL escaping**: All user input interpolated into WIQL strings must go through `_escape()` (doubles single quotes).
- **HTML conversion happens at export time**, not at fetch time. Raw HTML is stored in `WorkItem.description`, `repro_steps`, etc.
- **Error hierarchy**: `AzureDevOpsError` → `AuthenticationError` (401), `NotFoundError` (404), `RateLimitError` (429). The client retries 429/5xx with exponential backoff; 401/404 fail immediately.

## Testing

Tests mock at the `AzureDevOpsClient._request` level using `unittest.mock.patch`. Fixture JSON files in `tests/fixtures/` mirror real Azure DevOps API response shapes. No live API calls in tests.
