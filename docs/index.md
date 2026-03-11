# azwork

A terminal UI for triaging Azure DevOps work items. Browse, inspect, and export work items as Markdown — optimized for use as context in Claude Code sessions.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PyPI](https://img.shields.io/pypi/v/azwork)

![azwork demo](demo.gif)

## Features

- **Interactive TUI** — browse work items in a filterable, sortable table
- **Detail view** — inspect description, repro steps, comments, relations, and custom fields
- **Markdown export** — export any work item to a clean `.md` file
- **Claude Code prompt export** — generate a ready-to-use prompt wrapping the work item
- **Clipboard support** — copy Markdown to clipboard with a single keystroke
- **Smart caching** — fetched work items are cached in memory to keep navigation fast
- **HTML to Markdown** — Azure DevOps HTML content is automatically converted

## Quick install

```bash
pip install azwork
```

Then run the setup wizard:

```bash
export AZURE_DEVOPS_PAT="your-token-here"
azwork --setup
```

See [Getting Started](getting-started.md) for the full setup guide.

## How it works

```
azwork
  → WIQL query → Azure DevOps REST API
  → batch-fetch work item details (200/batch)
  → display in interactive TUI
  → export selected items as Markdown or Claude Code prompts
```

## Project structure

```
azwork/
├── __main__.py              # CLI entry point
├── config.py                # YAML config loading + CLI merge
├── utils.py                 # HTML → Markdown conversion
├── api/
│   ├── client.py            # Azure DevOps REST client
│   ├── wiql.py              # WIQL query builder
│   └── models.py            # WorkItem, Comment, Relation dataclasses
├── tui/
│   ├── app.py               # Textual App
│   ├── screens/             # List and Detail screens
│   └── widgets/             # FilterBar, ItemTable
└── export/
    ├── markdown.py          # Markdown generation
    └── prompt.py            # Claude Code prompt wrapper
```

## Requirements

- Python 3.10+
- An Azure DevOps organization with work items
- A PAT with **Work Items → Read** scope

## License

MIT
