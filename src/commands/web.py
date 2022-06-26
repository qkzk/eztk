from os import environ

from .command import exec_command

BROWSER = environ.get("BROWSER", "google-chrome-stable")


def open_in_browser(url: str) -> None:
    """Open the url in a default shell brother."""
    exec_command([BROWSER, url])
