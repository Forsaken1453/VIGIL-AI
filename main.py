"""
VIGIL - Entry point.

Jalankan GUI:      python main.py
Jalankan CLI:      python scripts/run_cli.py --help
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    try:
        from src.gui import main as gui_main
    except ImportError as exc:
        print(f"Dependency GUI belum terinstall: {exc}", file=sys.stderr)
        print("Jalankan: .venv\\Scripts\\pip install -r requirements.txt", file=sys.stderr)
        return 1
    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())