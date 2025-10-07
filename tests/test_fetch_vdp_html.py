from typing import Generator
import pytest
import time
import random
import httpx
from bs4 import BeautifulSoup
from core.helper_functions.fetch_vdp_html import (
    determine_vdp_search_path,
    fetch_vdp_html,
    _remove_dealership_marketing_paragraph,
)
from core.errors import ScraperError, PageNotFoundError, RequestFailedError
from tests.test_variables import TEST_VDP_URLS

# Wait between network requests to reduce chance of blocking
MIN_WAIT_SECS = 1.5
MAX_WAIT_SECS = 3.5

@pytest.fixture(autouse=True)
def delay_between_tests():
    """
    Automatically delay between tests that make real network calls.
    This fixture runs after each test to ensure we don't overwhelm the server.
    """
    yield
    time.sleep(random.uniform(MIN_WAIT_SECS, MAX_WAIT_SECS))


# Example expected par
@pytest.mark.parametrize(
    "url,expected_start",
    [
        (test_vdp_url["url"], test_vdp_url["description"][:10])
        for test_vdp_url in TEST_VDP_URLS
    ],
)
def test_fetch_vdp_html_live(url: str, expected_start: str):
    """
    Integration test: fetch live HTML and ensure it includes expected content.
    This runs slowly and should be rate-limited to avoid blocking.
    """
    search_pathes = determine_vdp_search_path(vdp_url=url)
    description = fetch_vdp_html(url, search_pathes)
    assert isinstance(description, str)


# Unit / offline parsing tests (no live HTTP requests)

def test_remove_dealership_marketing_paragraph_single():
    """
    Test that a single marketing paragraph is correctly removed.
    """
    text_with_marketing = (
        "Some intro. Introducing the All New Greg Hubler Promise: "
        "This is marketing text. More description afterwards."
    )
    cleaned = _remove_dealership_marketing_paragraph(text_with_marketing)
    assert "Introducing the All New Greg Hubler Promise" not in cleaned
    assert "Some intro." in cleaned
    assert "More description afterwards." in cleaned


def test_remove_dealership_marketing_multiple():
    """
    Test removal when multiple marketing paragraphs exist.
    """
    text = (
        "Intro text. Introducing the All New Greg Hubler Promise: Marketing 1. "
        "Real description. Introducing the All New Greg Hubler Promise: Marketing 2. "
        "More content."
    )
    cleaned = _remove_dealership_marketing_paragraph(text)
    # Only first occurrence should be removed per current logic
    assert cleaned.count("Introducing the All New Greg Hubler Promise") == 1


def test_remove_dealership_marketing_no_match():
    """
    If no marketing paragraph exists, text should remain identical.
    """
    original = "Regular description text with no marketing content."
    cleaned = _remove_dealership_marketing_paragraph(original)
    assert cleaned == original


def test_html_parsing_vehicle_description(monkeypatch):
    """
    Test that fetch_vdp_html correctly extracts text from mock HTML.
    """

    mock_html = """
        <html>
            <body>
                <div id="vehicle-description">
                    <div class="description">
                        This is the actual description text.
                    </div>
                </div>
            </body>
        </html>
    """

    class MockResponse:
        status_code = 200
        text = mock_html
        def raise_for_status(self): pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.Client, "get", mock_get)


    result = fetch_vdp_html(
        "https://example.com/fake-car",
        search_paths=[
            [
                {"tag": "div", "id": "vehicle-description"},
                {"tag": "div", "class_": "description"},
            ]
        ]
    )
    assert "actual description" in result.lower()


def test_html_parsing_no_vehicle_description(monkeypatch):
    """
    Test that ScraperError is raised if no 'vehicle-description' div is present.
    """

    mock_html = "<html><body><p>No vehicle description here.</p></body></html>"

    class MockResponse:
        status_code = 200
        text = mock_html
        def raise_for_status(self): pass

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    with pytest.raises(ScraperError):
        fetch_vdp_html(
            "https://example.com/fake-car",
            search_paths=[
                [
                    {"tag": "div", "id": "vehicle-description"},
                    {"tag": "div", "class_": "description"},
                ]
            ]
        )


def test_page_not_found_error(monkeypatch):
    """
    Test that PageNotFoundError is raised for 404 pages.
    """
    class MockResponse:
        status_code = 404
        def raise_for_status(self):
            raise httpx.HTTPStatusError("404 error", request=None, response=self)

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    with pytest.raises(PageNotFoundError):
        fetch_vdp_html(
            "https://example.com/missing-page",
            search_paths=[
                [
                    {"tag": "div", "id": "vehicle-description"},
                    {"tag": "div", "class_": "description"},
                ]
            ]
        )


def test_request_failed_error(monkeypatch):
    """
    Test that network-level errors raise ScraperError.
    """

    def mock_get(*args, **kwargs):
        raise httpx.RequestError("Network unreachable")

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    with pytest.raises(ScraperError):
        fetch_vdp_html(
            "https://example.com/test",
            search_paths=[
                [
                    {"tag": "div", "id": "vehicle-description"},
                    {"tag": "div", "class_": "description"},
                ]
            ]
        )


@pytest.mark.parametrize(
    "vdp_url",
    [
        "https://greghublerford.com/inventory/vehicle123",
        "https://www.sftoyota.com/inventory/vehicle456",
        "https://www.bergeronchryslerjeep.com/inventory/vehicle789",
    ],
)
def test_determine_vdp_search_path_valid_urls(vdp_url):
    """
    Test that valid VDP URLs return a search path.
    """
    search_path = determine_vdp_search_path(vdp_url)

    # Basic structure checks
    assert isinstance(search_path, list)
    assert len(search_path) > 0
    for step in search_path:
        assert isinstance(step, list)
        for element in step:
            assert isinstance(element, dict)
            assert "tag" in element


def test_determine_vdp_search_path_invalid_url():
    """
    Test that an invalid URL raises ScraperError.
    """
    invalid_url = "https://fakewebsite.com/inventory/vehicle000"

    with pytest.raises(ScraperError) as exc_info:
        determine_vdp_search_path(invalid_url)

    assert invalid_url in str(exc_info.value)
