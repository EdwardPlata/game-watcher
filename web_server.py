#!/usr/bin/env python3
"""
FastAPI web server for Sports Calendar application.
"""

import uvicorn
from api import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
