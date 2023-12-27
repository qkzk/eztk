from os import environ
from .command import exec_command, exec_command_shell

TERMINAL = environ.get("TERMINAL", "xterm")
EDITOR = environ.get("EDITOR", "nvim")


def open_in_ranger(address: str) -> None:
    """Open a path in the terminal with ranger."""
    exec_command([TERMINAL, "-e", "ranger", address])


def open_in_lvim_octo(address: str, number: int) -> None:
    """
    Open the issue in the terminal and the editor (nvim by default) with Octo.
    """
    exec_command_shell(
        f"""{TERMINAL} --working-directory {address} -e {EDITOR} +'Octo issue edit {number}'""",
    )
