#!/usr/bin/env python3
"""
Stock Market Dashboard - Main Entry Point

This is the main entry point for the stock market dashboard application.
It imports the Flask app from the back_end module and runs it.

Usage:
    python main.py
"""

from back_end.app import create_app
from back_end.config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

if __name__ == '__main__':
    app = create_app()
    print(f"🌐 Starting server on http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT) 