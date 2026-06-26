@echo off
title ── GIT-GHOST: CORE OBSERVER ENGINE ──
:: Set window size (Cols x Lines)
mode con: cols=85 lines=25
:: Set color scheme: 0 = Black Background, A = Light Green Text
color 0A
cls

cd /d "C:\Users\Charles\Desktop\GitGhost"
python watcher.py
pause