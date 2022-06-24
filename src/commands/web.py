from os import environ

from .command import exec_command

BROWSER = environ["BROWSER"]


def open_in_browser(url: str) -> None:
    exec_command([BROWSER, url])
