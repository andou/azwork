"""Azure DevOps REST API client."""

from __future__ import annotations

import time
from typing import Any

import requests

from azwork.api.models import Comment, WorkItem


API_VERSION = "7.0"
COMMENTS_API_VERSION = "7.0-preview.4"
BATCH_SIZE = 200
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0


class AzureDevOpsError(Exception):
    """Base error for API calls."""


class AuthenticationError(AzureDevOpsError):
    """PAT is invalid or missing required scope."""


class NotFoundError(AzureDevOpsError):
    """Organization or project not found."""


class RateLimitError(AzureDevOpsError):
    """Rate limit exceeded."""


class AzureDevOpsClient:
    """Client for Azure DevOps REST APIs."""

    def __init__(self, org: str, project: str, pat: str) -> None:
        self.org = org
        self.project = project
        self.base_url = f"https://dev.azure.com/{org}"
        self.session = requests.Session()
        self.session.auth = ("", pat)
        self.session.headers["Content-Type"] = "application/json"
        # In-memory cache for work items
        self._cache: dict[int, WorkItem] = {}

    def _request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Make an API request with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.request(method, url, json=json, params=params, timeout=30)
            except requests.ConnectionError:
                raise AzureDevOpsError(
                    "Unable to connect to Azure DevOps. Check your network connection."
                )
            except requests.Timeout:
                raise AzureDevOpsError("Request timed out. Please try again.")

            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed (401). Verify your AZURE_DEVOPS_PAT "
                    "and ensure it has 'Work Items → Read' scope."
                )
            if resp.status_code == 404:
                raise NotFoundError(
                    f"Not found (404). Verify org='{self.org}' and project='{self.project}' are correct."
                )
            if resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF * (2 ** attempt)
                    time.sleep(wait)
                    continue
                raise RateLimitError("Rate limit exceeded. Please wait and try again.")
            if resp.status_code >= 500:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF)
                    continue
                raise AzureDevOpsError(f"Server error ({resp.status_code}). Please try again later.")

            raise AzureDevOpsError(f"API error {resp.status_code}: {resp.text[:200]}")

        raise AzureDevOpsError("Max retries exceeded.")

    def query_work_item_ids(self, wiql: str) -> list[int]:
        """Execute a WIQL query and return work item IDs."""
        url = f"{self.base_url}/{self.project}/_apis/wit/wiql"
        params = {"api-version": API_VERSION}
        data = self._request("POST", url, json={"query": wiql}, params=params)
        return [item["id"] for item in data.get("workItems", [])]

    def get_work_items(
        self,
        ids: list[int],
        progress_callback: Any | None = None,
    ) -> list[WorkItem]:
        """Fetch work items by ID in batches. Returns cached items when available."""
        if not ids:
            return []

        # Separate cached vs uncached
        result: dict[int, WorkItem] = {}
        to_fetch: list[int] = []
        for wid in ids:
            if wid in self._cache:
                result[wid] = self._cache[wid]
            else:
                to_fetch.append(wid)

        # Fetch uncached in batches
        total_batches = (len(to_fetch) + BATCH_SIZE - 1) // BATCH_SIZE
        for batch_idx in range(total_batches):
            start = batch_idx * BATCH_SIZE
            batch_ids = to_fetch[start : start + BATCH_SIZE]
            ids_csv = ",".join(str(i) for i in batch_ids)

            url = f"{self.base_url}/_apis/wit/workitems"
            params = {
                "ids": ids_csv,
                "$expand": "all",
                "api-version": API_VERSION,
            }
            data = self._request("GET", url, params=params)

            for item_data in data.get("value", []):
                item = WorkItem.from_api(item_data)
                self._cache[item.id] = item
                result[item.id] = item

            if progress_callback:
                progress_callback(batch_idx + 1, total_batches)

        # Return in the original order
        return [result[wid] for wid in ids if wid in result]

    def get_comments(self, work_item_id: int) -> list[Comment]:
        """Fetch comments for a work item."""
        url = f"{self.base_url}/{self.project}/_apis/wit/workitems/{work_item_id}/comments"
        params = {"api-version": COMMENTS_API_VERSION}
        data = self._request("GET", url, params=params)
        return [Comment.from_api(c) for c in data.get("comments", [])]

    def get_fields(self) -> list[dict]:
        """Fetch all available fields for the project."""
        url = f"{self.base_url}/{self.project}/_apis/wit/fields"
        params = {"api-version": API_VERSION}
        data = self._request("GET", url, params=params)
        return data.get("value", [])

    def get_iterations(self) -> list[str]:
        """Fetch iteration paths for the project."""
        url = (
            f"{self.base_url}/{self.project}/_apis/wit/classificationnodes/iterations"
        )
        params = {"api-version": API_VERSION, "$depth": 10}
        try:
            data = self._request("GET", url, params=params)
            return _extract_paths(data, [])
        except AzureDevOpsError:
            return []

    def get_work_item_url(self, work_item_id: int) -> str:
        """Get the browser URL for a work item."""
        return f"https://dev.azure.com/{self.org}/{self.project}/_workitems/edit/{work_item_id}"

    def download_image(self, url: str) -> bytes:
        """Download an image from an authenticated Azure DevOps URL."""
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(url, timeout=30)
            except requests.ConnectionError:
                raise AzureDevOpsError("Unable to connect to download image.")
            except requests.Timeout:
                raise AzureDevOpsError("Image download timed out.")

            if resp.status_code == 200:
                return resp.content
            if resp.status_code == 401:
                raise AuthenticationError("Authentication failed downloading image.")
            if resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF * (2 ** attempt))
                    continue
                raise RateLimitError("Rate limit exceeded downloading image.")
            if resp.status_code >= 500 and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF)
                continue

            raise AzureDevOpsError(f"Failed to download image ({resp.status_code}).")

        raise AzureDevOpsError("Max retries exceeded downloading image.")

    def clear_cache(self) -> None:
        """Clear the work item cache."""
        self._cache.clear()


def _extract_paths(node: dict, parts: list[str]) -> list[str]:
    """Recursively extract iteration paths from classification node tree."""
    name = node.get("name", "")
    current_parts = [*parts, name] if name else parts
    path = "\\".join(current_parts)
    paths = [path] if path else []
    for child in node.get("children", []):
        paths.extend(_extract_paths(child, current_parts))
    return paths
