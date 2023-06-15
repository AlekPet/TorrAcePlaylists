@echo off
CALL ".\env\Scripts\activate.bat"
py get_torrserv_m3u.py
REM python -m http.server
REM py get_torrserv_m3u.py
pause