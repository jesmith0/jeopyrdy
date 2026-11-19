"""Run the game modules headless, from the app/ directory they expect."""
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(APP_DIR))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))
