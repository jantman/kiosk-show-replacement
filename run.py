#!/usr/bin/env python3
"""
Development server runner for kiosk-show-replacement.

This script provides a simple way to start the Flask development server
with proper environment configuration.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kiosk_show_replacement.app import create_app

if __name__ == '__main__':
    # Set environment variables if not already set
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', '1')
    
    # Create and run the app
    app = create_app()
    
    # Run the development server
    app.run(
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=True
    )
