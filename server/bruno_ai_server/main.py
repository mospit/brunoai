# Import the FastAPI app from the server root main.py
import sys
from pathlib import Path

# Add the server root directory to the path
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

from main import app
from bruno_ai_server.config import settings

__all__ = ["app", "settings"]
