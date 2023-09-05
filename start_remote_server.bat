@echo off
setlocal

:: Define the destination directory on the remote server and the remote IP
set REMOTE_DIR=/home/engtech/Documents/wifi_testing_server
set REMOTE_IP=10.10.100.132

:: Use PuTTY's PLINK to remotely kill any processes on port 5001
"C:\Program Files\PuTTY\plink.exe" -ssh engtech@%REMOTE_IP% -pw password2 "sudo fuser -k 5001/tcp"

:: Use PuTTY's PLINK to remotely run the Flask server
"C:\Program Files\PuTTY\plink.exe" -ssh engtech@%REMOTE_IP% -pw password2 "cd %REMOTE_DIR% && nohup python3 server.py > server_output.log 2>&1 &"

if errorlevel 1 (
    echo Failed to start server.
    exit /b 1
)

echo Flask server started successfully!
endlocal
