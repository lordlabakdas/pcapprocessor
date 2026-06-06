import subprocess


def exe_comm(cmd: list, capture: bool = True) -> str:
    """Run a shell command. Returns stdout as a string when capture=True."""
    if capture:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return result.stdout.decode("utf-8", errors="replace")
    subprocess.run(cmd, check=True)
    return ""
