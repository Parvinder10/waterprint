"""WATERPRINT: Intelligent Water Loss Detection and Network Analytics Platform.

Main Streamlit Cloud entry point.
Directly executes the operations dashboard from app/streamlit_app.py.
"""

import runpy
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).resolve().parent / "app" / "streamlit_app.py"
    runpy.run_path(str(app_path), run_name="__main__")
