from setuptools import setup

APP = ['./app/main.py']
DATA_FILES = [('', ['./app/res'])]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygame'],
    'iconfile': 'icon.icns'
}

setup(
    app=APP,
    version='0.1.0',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
