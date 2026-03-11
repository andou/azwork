# Usage

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

## Filtering

The list screen includes a filter bar at the top with:

- **Type** — filter by work item type (Bug, Task, User Story, etc.)
- **State** — filter by state (New, Active, Resolved, Closed, etc.)
- **Iteration** — filter by iteration path
- **Search** — free-text search across title and description

## Demo mode

Run azwork with fake data — useful for trying out the interface without an Azure DevOps connection:

```bash
azwork --demo
```

This loads 8 sample work items (bugs, tasks, user stories) with realistic titles, descriptions, and comments. No PAT or configuration is required.
