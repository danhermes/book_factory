#!/usr/bin/env python3
"""
Book Agent Editor - Kickoff Script
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV_PATH = PROJECT_ROOT / ".venv"

def activate_venv():
    if sys.prefix != str(VENV_PATH):
        if not VENV_PATH.exists():
            print(f"Error: Virtual environment not found at {VENV_PATH}")
            sys.exit(1)

        if sys.platform == "win32":
            venv_python = VENV_PATH / "Scripts" / "python.exe"
        else:
            venv_python = VENV_PATH / "bin" / "python"

        if not venv_python.exists():
            print(f"Error: Python not found at {venv_python}")
            sys.exit(1)

        os.execv(str(venv_python), [str(venv_python)] + sys.argv)

def main():
    activate_venv()

    import uvicorn
    from dotenv import load_dotenv

    sys.path.insert(0, str(PROJECT_ROOT))
    os.chdir(PROJECT_ROOT)
    load_dotenv()

    host = os.getenv("BOOK_AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("BOOK_AGENT_PORT", "8000"))

    print(f"""
╔══════════════════════════════════════════════════════════╗
║                   Book Agent Editor                       ║
╠══════════════════════════════════════════════════════════╣
║  Server: http://localhost:{port:<5}                          ║
║  Model:  {os.getenv('AGENT_MODEL', 'gpt-4o'):<15}                            ║
║  Temp:   {os.getenv('AGENT_TEMPERATURE', '0.7'):<5}                                    ║
║  Press Ctrl+C to stop                                     ║
╚══════════════════════════════════════════════════════════╝
""")

    uvicorn.run(
        "src.book_agent.app:app",
        host=host,
        port=port,
        reload=False
    )


# For direct uvicorn usage: uvicorn src.book_agent.app:app

if __name__ == "__main__":
    main()
