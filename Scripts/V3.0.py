import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_window import run_app

# GPIO Control Panel Version
VERSION = "v6.0 - Piedmont Edition"

# Teacher Mode Configuration
# Change this password as needed for your classroom security
TEACHER_PASSWORD = "Training"

# GPIO Control Panel V3.0
# Automatically clears all configurations on startup for classroom use
# To keep existing configs for debugging, run with: python V3.0.py --keep-config

def get_version():
    """Get the current version string"""
    return VERSION

def get_teacher_password():
    """Get the current teacher password"""
    return TEACHER_PASSWORD

if __name__ == "__main__":
    run_app()