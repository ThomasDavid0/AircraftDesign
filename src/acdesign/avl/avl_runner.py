import subprocess
from pathlib import Path


def run_avl(commands: list[str]) -> None:
    """Run AVL with the specified commands.

    Args:
        commands (list[str]): A list of commands to be executed in AVL.
    """

    process = subprocess.Popen(
        "./avl",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path("avl"),
    )
    process.stdin.write("\n".join(commands).encode())
    output, error = process.communicate()
    if error:
        raise RuntimeError(f"AVL Error: {error.decode()}")
    return output




if __name__ == "__main__":
    run_avl(["load MACE1.avl", "OPER", "a c 0.2", "x", "ft avlout.txt", " ", "QUIT"])
