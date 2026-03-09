"""Configuration loading from ~/.azwork.yml and CLI args."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


CONFIG_PATH = Path.home() / ".azwork.yml"


@dataclass
class Config:
    org: str = ""
    project: str = ""
    default_output_dir: str = "./bugs"
    work_item_types: list[str] = field(default_factory=lambda: ["Bug", "Task", "User Story"])
    prompt_template: str = ""
    pat: str = ""

    @classmethod
    def load(cls, cli_org: str | None = None, cli_project: str | None = None,
             cli_output_dir: str | None = None) -> Config:
        cfg = cls()

        # Load from YAML if exists
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH) as f:
                    data = yaml.safe_load(f) or {}
                cfg.org = data.get("org", "")
                cfg.project = data.get("project", "")
                cfg.default_output_dir = data.get("default_output_dir", "./bugs")
                cfg.work_item_types = data.get("work_item_types", cfg.work_item_types)
                cfg.prompt_template = data.get("prompt_template", "")
            except Exception:
                pass

        # CLI overrides
        if cli_org:
            cfg.org = cli_org
        if cli_project:
            cfg.project = cli_project
        if cli_output_dir:
            cfg.default_output_dir = cli_output_dir

        # PAT from environment
        cfg.pat = os.environ.get("AZURE_DEVOPS_PAT", "")

        return cfg

    def save_default(self) -> None:
        data = {
            "org": self.org,
            "project": self.project,
            "default_output_dir": self.default_output_dir,
            "work_item_types": self.work_item_types,
        }
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def validate(self) -> list[str]:
        errors = []
        if not self.pat:
            errors.append(
                "AZURE_DEVOPS_PAT environment variable is not set.\n"
                "Create a PAT at https://dev.azure.com/{org}/_usersSettings/tokens\n"
                "Required scope: Work Items → Read"
            )
        if not self.org:
            errors.append("Organization not set. Use --org or set 'org' in ~/.azwork.yml")
        if not self.project:
            errors.append("Project not set. Use --project or set 'project' in ~/.azwork.yml")
        return errors
