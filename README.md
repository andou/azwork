# azwork

A terminal UI for triaging Azure DevOps work items. Browse, inspect, and export work items as Markdown — optimized for use as context in Claude Code sessions.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Interactive TUI** — browse work items in a filterable, sortable table
- **Detail view** — inspect description, repro steps, comments, relations, and custom fields
- **Markdown export** — export any work item to a clean `.md` file
- **Claude Code prompt export** — generate a ready-to-use prompt wrapping the work item
- **Clipboard support** — copy Markdown to clipboard with a single keystroke
- **Smart caching** — fetched work items are cached in memory to keep navigation fast
- **HTML → Markdown** — Azure DevOps HTML content is automatically converted

## Installation

```bash
pip install azwork
```

Or install from source:

```bash
git clone https://github.com/a-pastorino/azwork.git
cd azwork
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick start

### 1. Create a Personal Access Token

Go to `https://dev.azure.com/{your-org}/_usersSettings/tokens` and create a token with the **Work Items → Read** scope.

Export it as an environment variable:

```bash
export AZURE_DEVOPS_PAT="your-token-here"
```

### 2. Run the setup wizard

```bash
azwork --setup
```

This creates `~/.azwork.yml` interactively.

### 3. Launch

```bash
azwork
```

## Usage

```bash
# Use defaults from ~/.azwork.yml
azwork

# Override org and project
azwork --org myorg --project myproject

# Custom export directory
azwork --output-dir ./sprint-bugs

# Re-run setup
azwork --setup
```

## Configuration

azwork reads its configuration from `~/.azwork.yml`. CLI arguments always take priority.

### `~/.azwork.yml` anatomy

```yaml
# Azure DevOps organization name (the {org} part of dev.azure.com/{org})
org: myorg

# Project name within the organization
project: myproject

# Default directory where exported Markdown files are saved.
# Can be an absolute path or relative to where you run azwork.
# Created automatically on first export if it doesn't exist.
default_output_dir: ./bugs

# Work item types to include in queries.
# These are used both as WIQL filter and as options in the Type dropdown.
# Common values: Bug, Task, User Story, Epic, Feature, Issue, Test Case
work_item_types:
  - Bug
  - Task
  - User Story
```

All fields are optional when using CLI overrides. The PAT is **never** stored in the config file — it is always read from the `AZURE_DEVOPS_PAT` environment variable.

### Minimal example

```yaml
org: contoso
project: webapp
```

### Full example

```yaml
org: contoso
project: webapp
default_output_dir: ~/work/bugs
work_item_types:
  - Bug
  - Task
  - User Story
  - Feature
  - Epic
```

## Keybindings

### List screen

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate rows |
| `Enter` | Open detail view |
| `E` | Export highlighted item to Markdown |
| `R` | Refresh (re-fetch from API) |
| `Q` | Quit |
| `?` | Show help |

Column headers are clickable to sort by that column.

### Detail screen

| Key | Action |
|-----|--------|
| `Esc` | Back to list |
| `E` | Export as Markdown |
| `P` | Export as Claude Code prompt |
| `C` | Copy Markdown to clipboard |
| `O` | Open in browser |
| `?` | Show help |

## Export formats

### Markdown

A structured Markdown file with metadata table, description, repro steps, acceptance criteria, discussion thread, related items, and custom fields.

```
bugs/1234-login-fails-special-chars.md
```

### Claude Code prompt

Same Markdown content wrapped in a prompt template that instructs Claude Code to analyze and resolve the work item:

```markdown
# Task: Resolve the following work item

Analyze the work item described below and take the necessary actions to resolve it.
The project context is described in the CLAUDE.md file at the repository root.

## Work Item
[... full work item markdown ...]

## Instructions
1. Analyze the work item and identify the affected files
2. Implement the fix or the requested feature
3. Write or update tests to cover the case
4. Verify that existing tests are not broken
5. Briefly describe the changes you made
```

## Project structure

```
azwork/
├── __main__.py              # CLI entry point (argparse)
├── config.py                # YAML config loading + CLI merge
├── utils.py                 # HTML→Markdown conversion
├── api/
│   ├── client.py            # Azure DevOps REST client (auth, batching, cache)
│   ├── wiql.py              # WIQL query builder
│   └── models.py            # WorkItem, Comment, Relation dataclasses
├── tui/
│   ├── app.py               # Textual App
│   ├── screens/
│   │   ├── list_screen.py   # Work item list with filters
│   │   └── detail_screen.py # Single item detail + export dialog
│   └── widgets/
│       ├── filter_bar.py    # Type / State / Iteration / Search filters
│       └── item_table.py    # Sortable DataTable for work items
└── export/
    ├── markdown.py          # Markdown generation
    └── prompt.py            # Claude Code prompt wrapper
```

## Running tests

```bash
pytest
```

Tests mock all API calls and cover:

- API client (pagination, HTTP errors, caching, response parsing)
- WIQL query construction with various filter combinations
- Markdown export (formatting, edge cases, empty fields)
- HTML → Markdown conversion (all supported tags)

## Requirements

- Python 3.10+
- An Azure DevOps organization with work items
- A PAT with **Work Items → Read** scope

## License

MIT
