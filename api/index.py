import os
import sys

# Ensure backend modules are available in Python path on serverless runtime
sys.path.insert(0, os.path.abspath("."))

from backend.main import app

# Handler for Vercel Serverless
app = app
