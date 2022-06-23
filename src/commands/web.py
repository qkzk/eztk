from os import environ
import subprocess
import warnings

warnings.filterwarnings("ignore")
BROWSER = environ["BROWSER"]


def open_in_browser(url: str) -> None:
    subprocess.Popen(
        [BROWSER, url],
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
