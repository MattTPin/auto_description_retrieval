import pytest
from bs4 import BeautifulSoup
import httpx
from client.scrape_html import scrape_html  # adjust import as needed
from core.errors import PageNotFoundError, RequestFailedError, ScraperError

def test_scrape_html_real_site():
    """
    Test that scrape_html successfully fetches and parses a known stable URL.
    Verifies that the returned object is a BeautifulSoup instance and contains
    expected HTML elements.
    """
    url = "https://example.com"
    soup = scrape_html(url)
    assert isinstance(soup, BeautifulSoup)
    assert soup.find("h1").text.strip() == "Example Domain"


def test_scrape_html_404(monkeypatch):
    """
    Test that scrape_html raises PageNotFoundError when a 404 HTTP status is returned.
    """

    url = "https://example.com/notfound"

    class MockResponse:
        status_code = 404

        def raise_for_status(self):
            raise httpx.HTTPStatusError("Not Found", request=None, response=self)

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr("httpx.Client", MockClient)

    with pytest.raises(PageNotFoundError) as exc_info:
        scrape_html(url)
    assert "Page not found" in str(exc_info.value)


def test_scrape_html_http_error(monkeypatch):
    """
    Test that scrape_html raises RequestFailedError for non-404 HTTP errors.
    """

    url = "https://example.com/error"

    class MockResponse:
        status_code = 500

        def raise_for_status(self):
            raise httpx.HTTPStatusError("Server Error", request=None, response=self)

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr("httpx.Client", MockClient)

    with pytest.raises(RequestFailedError) as exc_info:
        scrape_html(url)
    assert "HTTP request failed" in str(exc_info.value)


def test_scrape_html_request_error(monkeypatch):
    """
    Test that scrape_html raises ScraperError when an httpx.RequestError occurs,
    simulating network issues.
    """

    url = "https://example.com/networkfail"

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            raise httpx.RequestError("Connection failed")

    monkeypatch.setattr("httpx.Client", MockClient)

    with pytest.raises(ScraperError) as exc_info:
        scrape_html(url)
    assert "Could not retrieve page" in str(exc_info.value)