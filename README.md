# THIS IS JEOPYRDY
[![CI](https://github.com/jesmith0/jeopyrdy/actions/workflows/ci.yml/badge.svg)](https://github.com/jesmith0/jeopyrdy/actions/workflows/ci.yml)

multi-player celebrity Jeopardy simulator using [pygame-ce](https://pyga.me/) with support for [PS2 "BUZZ!" controllers](https://www.ebay.com/p/1234467844)

![](app/res/images/chars.png)

## Install (Requires Python 3.10+)
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```python app/main.py```

## Test
```
pip install pytest ruff
ruff check .
pytest
```

## Build

##### For Mac
```
pip install py2app
python build.py py2app
```
##### Windows coming soon

### This project is dedicated to the memory of Alex Trebek
![](app/res/images/alex.png)  
[Donate to National Pancreatic Cancer Foundation!](https://www.npcf.us/ways-to-donate/)
