"""
setup.py - script for building MyApplication

Usage:
    % python jeopardy2app.py py2app
"""

from distutils.core import setup
import py2app

setup(
    app=['main.py'],
)