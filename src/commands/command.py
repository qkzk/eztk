import subprocess
import warnings

# used to prevent mallog warnings when running commands.
warnings.filterwarnings("ignore")


def exec_command(command: list[str]) -> None:
    """
    Run an sh command directly.
    stdout and stderr are both redirected to DEVNULL.
    Command must be a list of string.
    Allow us to close the mainapp without killing the spawned process.
    """
    subprocess.Popen(
        command,
        shell=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def exec_command_shell(command: str) -> None:
    """
    Run a sh command through a shell instance.
    stdout and stderr are both redirected to DEVNULL.
    Command is a string.
    Allow us to close the mainapp without killing the spawned process.
    """
    subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
