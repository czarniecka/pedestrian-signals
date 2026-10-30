"""Start local Label Studio on Windows, Linux or macOS.

Usage: python scripts/start_label_studio.py
Uses .venv-label-studio when available, otherwise label-studio from PATH.
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = (
        ROOT / ".venv-label-studio" / "Scripts" / "label-studio.exe"
        if os.name == "nt"
        else ROOT / ".venv-label-studio" / "bin" / "label-studio"
    )
    launcher = str(executable) if executable.is_file() else shutil.which("label-studio")
    if not launcher:
        print(
            "Label Studio was not found in .venv-label-studio or PATH. "
            "Install it using the instructions in docs/IMPORTED_WORK.md.",
            file=sys.stderr,
        )
        return 1

    env = os.environ.copy()
    env.update({
        "LABEL_STUDIO_BASE_DATA_DIR": str(ROOT / ".label-studio"),
        "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED": "true",
        "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT": str(ROOT / "data" / "raw" / "images"),
        "LABEL_STUDIO_DISABLE_TELEMETRY": "true",
        "PYTHONUTF8": "1",
    })
    try:
        return subprocess.call(
            [launcher, "start", "--port", "8080", "--internal-host", "127.0.0.1"],
            cwd=ROOT,
            env=env,
        )
    except KeyboardInterrupt:
        return 130
    except OSError as error:
        print(f"Could not start Label Studio: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
