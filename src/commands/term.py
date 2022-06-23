from os import environ
import subprocess

TERMINAL = environ["TERMINAL"]
EDITOR = environ["EDITOR"]


def open_in_ranger(address: str) -> None:
    subprocess.Popen(
        [TERMINAL, "-e", "ranger", address],
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def open_in_lvim_octo(address: str, number: int) -> None:
    subprocess.Popen(
        f"""{TERMINAL} -d {address} -e {EDITOR} +'Octo issue edit {number}'""",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
