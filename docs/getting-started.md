# Getting Started

## Installation

=== "From PyPI"

    ```bash
    pip install azwork
    ```

=== "From source"

    ```bash
    git clone https://github.com/andou/azwork.git
    cd azwork
    pip install .
    ```

=== "Development"

    ```bash
    git clone https://github.com/andou/azwork.git
    cd azwork
    pip install -e ".[dev]"
    ```

## Create a Personal Access Token

Go to `https://dev.azure.com/{your-org}/_usersSettings/tokens` and create a token with the **Work Items → Read** scope.

Export it as an environment variable:

```bash
export AZURE_DEVOPS_PAT="your-token-here"
```

!!! warning
    The PAT is **never** stored in the config file — it is always read from the `AZURE_DEVOPS_PAT` environment variable.

## Run the setup wizard

```bash
azwork --setup
```

This creates `~/.azwork.yml` interactively, asking for your organization name, project, and preferred work item types.

## Launch

```bash
azwork
```

## Configuration

azwork reads its configuration from `~/.azwork.yml`. CLI arguments always take priority.

### Config file anatomy

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
work_item_types:
  - Bug
  - Task
  - User Story
```

All fields are optional when using CLI overrides.

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

### CLI overrides

```bash
# Override org and project
azwork --org myorg --project myproject

# Custom export directory
azwork --output-dir ./sprint-bugs
```
