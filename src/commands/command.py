import subprocess
import warnings


warnings.filterwarnings("ignore")


def exec_command(command: list[str]) -> None:
    subprocess.Popen(
        command,
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def exec_command_shell(command: str) -> None:
    subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
