@echo off
if exist .venv\Scripts\python.exe exit /b 0
echo Pierwsze uruchomienie: instaluje zaleznosci...
python -m venv .venv || exit /b 1
.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu || exit /b 1
.venv\Scripts\python.exe -m pip install stable-baselines3[extra] gymnasium pyzmq numpy || exit /b 1
