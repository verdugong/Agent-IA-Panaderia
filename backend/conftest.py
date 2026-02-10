# Pytest configuration - adds backend to Python path
import sys
from pathlib import Path

# Add backend folder to path so 'app' is importable
sys.path.insert(0, str(Path(__file__).parent))
