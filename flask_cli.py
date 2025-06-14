#!/usr/bin/env python3
"""
Flask CLI entry point for kiosk-show-replacement.

This script provides a Flask CLI interface for database management,
server operations, and other administrative tasks.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kiosk_show_replacement.app import create_app

def main():
    """Main entry point for Flask CLI."""
    os.environ.setdefault('FLASK_ENV', 'development')
    app = create_app()
    
    # Set Flask app for CLI
    os.environ['FLASK_APP'] = 'app.py'
    
    # Run Flask CLI
    from flask.cli import main as flask_main
    flask_main()

if __name__ == '__main__':
    main()
