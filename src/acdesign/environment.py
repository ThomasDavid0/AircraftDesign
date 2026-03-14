from dotenv import load_dotenv
from os import getenv
from pathlib import Path

load_dotenv(override=True)

AVL_PROGRAM = getenv("AVL_PROGRAM", "avl")
AVL_WORKSPACE = getenv("AVL_WORKSPACE", "/tmp/avl_workspace")

Path(AVL_WORKSPACE).mkdir(parents=True, exist_ok=True)