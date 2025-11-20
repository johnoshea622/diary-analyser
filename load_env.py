#!/usr/bin/env python3
"""
Load environment variables from .env file.
Import this at the top of scripts that need API access.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root
project_root = Path(__file__).parent
env_path = project_root / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"Warning: .env file not found at {env_path}")
