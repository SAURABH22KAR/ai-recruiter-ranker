@echo off
echo Starting AI Recruiter...
echo.

:: Start backend
start "AI Recruiter - Backend" cmd /k "cd backend && C:\Users\bavis\anaconda3\python.exe -m uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

:: Start frontend
start "AI Recruiter - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo To generate the submission CSV (offline, no API key needed):
echo   C:\Users\bavis\anaconda3\python.exe rank.py
