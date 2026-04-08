@echo off
for /f  tokens=5 %%p in ('netstat -ano ^| findstr :8003 ^| findstr LISTENING') do taskkill /PID %%p /F
for /f tokens=5 %%p in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do taskkill /PID %%p /F
for /f tokens=5 %%p in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %%p /F
