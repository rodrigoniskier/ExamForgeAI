"""Prepare only an explicitly selected synthetic demo database at build time."""
import os
import subprocess
import sys

if os.environ.get("PORTFOLIO_DEMO") == "1":
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("A dedicated DATABASE_URL is required for the demo build")
    for command in (["migrate", "--noinput"], ["seed_demo"]):
        subprocess.run([sys.executable, "manage.py", *command], check=True)
