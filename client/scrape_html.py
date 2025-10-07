"""
Generic reusable HTML scraping utility.
"""

import httpx
from bs4 import BeautifulSoup

from core.errors import ScraperError, PageNotFoundError, RequestFailedError


def scrape_html(url: str) -> BeautifulSoup:
    """
    Retrieve and parse an HTML document from a given URL using `httpx`.

    Sends a GET request with browser-like headers, then returns a BeautifulSoup
    object for further HTML processing. Raises meaningful errors for various
    failure conditions.

    Args:
        url (str): The web page URL to fetch.

    Returns:
        BeautifulSoup: Parsed HTML content.

    Raises:
        PageNotFoundError: If the page returns a 404 status.
        RequestFailedError: If another non-200 HTTP status is returned.
        ScraperError: For network or parsing errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.6261.57 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise PageNotFoundError(
                message="Page not found",
                url=url,
                status_code=e.response.status_code
            ) from e
        raise RequestFailedError(
            message="HTTP request failed",
            url=url,
            status_code=e.response.status_code
        ) from e
    except httpx.RequestError as e:
        raise ScraperError(
            message=f"Could not retrieve page: {str(e)}",
            url=url
        ) from e

    return BeautifulSoup(response.text, "html.parser")
