# JeoPyrdy
multi-player celebrity Jeopardy simulator using [PyGame](https://www.pygame.org/) with support for [PS2 "BUZZ!" controllers](https://www.ebay.com/p/1234467844)
![](res/images/chars.png)

## Install (Requires Python 2.7)
```pip install -r requirements.txt```

## Run
```cd src && python main.py```

## Build
As a result of the recent refactor, these scripts are very unlikely to work though I'm not sure they ever did in the first place.
##### For Windows
```
pip install pywin32 py2exe
python scripts/2exe.py
```
##### For Mac
```
pip install py2app
python scripts/2app.py
```