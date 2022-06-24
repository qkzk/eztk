from os import environ
import subprocess

from .command import exec_command, exec_command_shell

TERMINAL = environ["TERMINAL"]
EDITOR = environ["EDITOR"]


def open_in_ranger(address: str) -> None:
    exec_command([TERMINAL, "-e", "ranger", address])


def open_in_lvim_octo(address: str, number: int) -> None:
    exec_command_shell(
        f"""{TERMINAL} -d {address} -e {EDITOR} +'Octo issue edit {number}'""",
    )
