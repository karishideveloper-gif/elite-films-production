"""
WSGI entry point for production deployment.
Use this with production WSGI servers like Gunicorn, uWSGI, etc.

Example usage:
  gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
"""

import os
from dotenv import load_dotenv
from app import app

# Load environment variables
load_dotenv()

