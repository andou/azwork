"""Tests for the Azure DevOps API client."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from azwork.api.client import (
    AuthenticationError,
    AzureDevOpsClient,
    AzureDevOpsError,
    NotFoundError,
    RateLimitError,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    return AzureDevOpsClient(org="myorg", project="myproject", pat="fake-pat")


@pytest.fixture
def wiql_response():
    with open(FIXTURES / "sample_wiql_response.json") as f:
        return json.load(f)


@pytest.fixture
def workitem_response():
    with open(FIXTURES / "sample_workitem_response.json") as f:
        return json.load(f)


def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


class TestQueryWorkItemIds:
    @patch.object(AzureDevOpsClient, "_request")
    def test_returns_ids(self, mock_request, client, wiql_response):
        mock_request.return_value = wiql_response
        ids = client.query_work_item_ids("SELECT [System.Id] FROM WorkItems")
        assert ids == [1234, 1235, 1236]

    @patch.object(AzureDevOpsClient, "_request")
    def test_empty_result(self, mock_request, client):
        mock_request.return_value = {"workItems": []}
        ids = client.query_work_item_ids("SELECT [System.Id] FROM WorkItems")
        assert ids == []


class TestGetWorkItems:
    @patch.object(AzureDevOpsClient, "_request")
    def test_fetches_items(self, mock_request, client, workitem_response):
        mock_request.return_value = workitem_response
        items = client.get_work_items([1234, 1235])
        assert len(items) == 2
        assert items[0].id == 1234
        assert items[0].title == "Login fails with special chars"
        assert items[0].work_item_type == "Bug"
        assert items[0].state == "Active"
        assert items[0].priority == 1
        assert items[0].assigned_to == "Marco Rossi"

    @patch.object(AzureDevOpsClient, "_request")
    def test_caches_items(self, mock_request, client, workitem_response):
        mock_request.return_value = workitem_response
        client.get_work_items([1234, 1235])
        # Second call should not hit API
        mock_request.reset_mock()
        items = client.get_work_items([1234])
        assert len(items) == 1
        assert items[0].id == 1234
        mock_request.assert_not_called()

    def test_empty_ids(self, client):
        assert client.get_work_items([]) == []

    @patch.object(AzureDevOpsClient, "_request")
    def test_progress_callback(self, mock_request, client, workitem_response):
        mock_request.return_value = workitem_response
        callback = MagicMock()
        client.get_work_items([1234, 1235], progress_callback=callback)
        callback.assert_called_once_with(1, 1)

    @patch.object(AzureDevOpsClient, "_request")
    def test_custom_fields_extracted(self, mock_request, client, workitem_response):
        mock_request.return_value = workitem_response
        items = client.get_work_items([1234])
        item = items[0]
        assert "Custom.RootCause" in item.custom_fields
        assert item.custom_fields["Custom.RootCause"] == "Input Sanitization"

    @patch.object(AzureDevOpsClient, "_request")
    def test_relations_extracted(self, mock_request, client, workitem_response):
        mock_request.return_value = workitem_response
        items = client.get_work_items([1234])
        item = items[0]
        assert len(item.relations) == 1
        assert item.relations[0].rel_type == "Parent"
        assert item.relations[0].target_id == 1200


class TestHttpErrors:
    def test_401_raises_auth_error(self, client):
        with patch("requests.Session.request", return_value=_mock_response(401)):
            with pytest.raises(AuthenticationError):
                client._request("GET", "https://example.com")

    def test_404_raises_not_found(self, client):
        with patch("requests.Session.request", return_value=_mock_response(404)):
            with pytest.raises(NotFoundError):
                client._request("GET", "https://example.com")

    def test_429_retries_and_raises(self, client):
        with patch("requests.Session.request", return_value=_mock_response(429)):
            with patch("time.sleep"):
                with pytest.raises(RateLimitError):
                    client._request("GET", "https://example.com")

    def test_connection_error(self, client):
        import requests as req
        with patch("requests.Session.request", side_effect=req.ConnectionError):
            with pytest.raises(AzureDevOpsError, match="Unable to connect"):
                client._request("GET", "https://example.com")

    def test_timeout_error(self, client):
        import requests as req
        with patch("requests.Session.request", side_effect=req.Timeout):
            with pytest.raises(AzureDevOpsError, match="timed out"):
                client._request("GET", "https://example.com")


class TestDownloadImage:
    def test_success(self, client):
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b"\x89PNG fake image data"
        with patch("requests.Session.get", return_value=resp):
            data = client.download_image("https://dev.azure.com/org/_apis/wit/attachments/abc")
        assert data == b"\x89PNG fake image data"

    def test_401_raises_auth_error(self, client):
        resp = MagicMock()
        resp.status_code = 401
        with patch("requests.Session.get", return_value=resp):
            with pytest.raises(AuthenticationError):
                client.download_image("https://dev.azure.com/org/_apis/wit/attachments/abc")

    def test_connection_error(self, client):
        import requests as req
        with patch("requests.Session.get", side_effect=req.ConnectionError):
            with pytest.raises(AzureDevOpsError, match="Unable to connect"):
                client.download_image("https://example.com/img.png")


class TestClearCache:
    @patch.object(AzureDevOpsClient, "_request")
    def test_clear_cache(self, mock_request, client, workitem_response):
        mock_request.return_value = workitem_response
        client.get_work_items([1234])
        assert 1234 in client._cache
        client.clear_cache()
        assert len(client._cache) == 0
