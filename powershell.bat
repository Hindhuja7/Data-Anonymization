@echo off
set CMD=%*
set CMD=%CMD:-Command =%
set CMD=%CMD:\"=%
python %CMD%
