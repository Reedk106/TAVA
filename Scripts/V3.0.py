import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_window import run_app

# GPIO Control Panel Version
VERSION = "V4.0 - Piedmont Edition"

# GPIO Control Panel V3.0
# Automatically clears all configurations on startup for classroom use
# To keep existing configs for debugging, run with: python V3.0.py --keep-config

def get_version():
    """Get the current version string"""
    return VERSION

if __name__ == "__main__":
    run_app()