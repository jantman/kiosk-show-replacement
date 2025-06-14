#!/usr/bin/env python3
"""
Standalone database initialization script for kiosk-show-replacement.

This script can be run independently to initialize the database.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the initialization function from our package
from kiosk_show_replacement.cli.init_db import main

if __name__ == '__main__':
    main()
