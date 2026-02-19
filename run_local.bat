@echo off
cd /d "%~dp0"

set API_ID=30582273
set API_HASH=5c34ecdcab83332e4850e01270d84bba
set SOURCE_CHANNEL=Avibum
set DEST_CHANNEL=KE7ZONE

echo Starting repost bot locally...
python repost.py
pause
