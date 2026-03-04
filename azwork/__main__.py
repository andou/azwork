"""CLI entry point for azwork."""

from __future__ import annotations

import argparse
import sys

from azwork.config import Config, CONFIG_PATH


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="azwork",
        description="TUI for triaging Azure DevOps work items",
    )
    parser.add_argument("--org", help="Azure DevOps organization")
    parser.add_argument("--project", help="Azure DevOps project")
    parser.add_argument("--output-dir", help="Default output directory for exports")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard")

    args = parser.parse_args()

    if args.setup:
        _run_setup()
        return

    config = Config.load(
        cli_org=args.org,
        cli_project=args.project,
        cli_output_dir=args.output_dir,
    )

    # If no config exists and no CLI args, run setup
    if not config.org or not config.project:
        if not CONFIG_PATH.exists():
            print("No configuration found. Running setup wizard...")
            _run_setup()
            config = Config.load(
                cli_org=args.org,
                cli_project=args.project,
                cli_output_dir=args.output_dir,
            )
        else:
            errors = config.validate()
            for err in errors:
                print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

    errors = config.validate()
    if errors:
        for err in errors:
            print(f"Error: {err}", file=sys.stderr)
        sys.exit(1)

    from azwork.tui.app import AzworkApp

    app = AzworkApp(config)
    app.run()


def _run_setup() -> None:
    """Interactive setup wizard to create ~/.azwork.yml."""
    print("=== azwork Setup ===\n")

    org = input("Azure DevOps Organization: ").strip()
    project = input("Project name: ").strip()
    output_dir = input("Default export directory [./bugs]: ").strip() or "./bugs"
    types_input = input("Work item types (comma-separated) [Bug,Task,User Story]: ").strip()
    types = [t.strip() for t in types_input.split(",")] if types_input else ["Bug", "Task", "User Story"]

    config = Config(
        org=org,
        project=project,
        default_output_dir=output_dir,
        work_item_types=types,
    )
    config.save_default()
    print(f"\nConfiguration saved to {CONFIG_PATH}")
    print("Set AZURE_DEVOPS_PAT environment variable with your Personal Access Token.")
    print("Run 'azwork' to start.")


if __name__ == "__main__":
    main()
