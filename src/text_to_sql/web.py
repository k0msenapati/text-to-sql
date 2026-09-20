import subprocess
import sys
from pathlib import Path


def run():
    """Launches the Chainlit web interface."""
    root_app = Path.cwd() / "app.py"
    repo_app = Path(__file__).resolve().parent.parent.parent / "app.py"

    if root_app.exists():
        target = str(root_app)
    elif repo_app.exists():
        target = str(repo_app)
    else:
        target = "app.py"

    cmd = [sys.executable, "-m", "chainlit", "run", target] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    run()
