@echo off
echo Setting up AI Recruiter Backend...
echo Using Anaconda Python at C:\Users\bavis\anaconda3\python.exe

C:\Users\bavis\anaconda3\python.exe -m pip install -r requirements.txt

echo.
echo Setup complete!
echo Copy .env.example to .env and add your ANTHROPIC_API_KEY.
echo Then run: start.bat
