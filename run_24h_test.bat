@echo off
REM BrewXOS 24h 串口测试启动器
REM 用法: 双击这个文件，或者在 cmd 里 run_24h_test.bat

setlocal

REM 切到 igem 目录
cd /d "C:\Users\xiaomi\Desktop\igem"

REM 用项目 venv 的 python
set PYTHON="C:\Users\xiaomi\Desktop\igem\venv\Scripts\python.exe"

REM 默认 COM5 + data 目录
REM 如果你 Arduino 在别的 COM 口，编辑下面的 --port
%PYTHON% serial_24h_logger.py --port COM5 --out data\run_20260812.csv --duration 24h

pause
