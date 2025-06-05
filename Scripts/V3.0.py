import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_window import run_app

if __name__ == "__main__":
    run_app()