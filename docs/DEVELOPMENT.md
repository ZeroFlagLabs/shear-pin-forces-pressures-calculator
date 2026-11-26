# Development

Windows, Python 3.13.16, PySide6 6.12.0. Create a .venv and install requirements-build.txt. Run tools/run_app.bat or .venv/Scripts/python.exe src/main.py. The main window is programmatic Qt; Settings uses a Designer UI file. The original single-plane calculator function is retained for regression comparison; evaluate() implements the validated multi-plane, adjustable-factor range calculation. Settings and Inspect Results use Designer forms.

Run .venv/Scripts/python.exe -m unittest discover -s tests and each tests/check_*.py in a normal Windows desktop session (not headless). Test output goes to ignored private documentation. Build with .venv/Scripts/python.exe tools/Build-OneFile-Portable.py --output releases/v2.0.0. The builder verifies archive contents and creates a ZIP and SHA-256 sidecar. Run the extracted executable with --self-test --self-test-output <absolute JSON path> for frozen functional checks.

The single-file EXE contains the runtime; see [third-party notices](THIRD_PARTY_NOTICES.md) and [rebuild instructions](ONEFILE_REBUILD_AND_LGPL.md). No installation privilege required.
