"""
FastAPI web application package.
"""

from .app import create_app
from .models import *
from .routes import *

__all__ = ['create_app']
