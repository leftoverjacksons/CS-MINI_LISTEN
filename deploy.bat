@echo off
setlocal

:: Define the paths to the local files and the destination directory on the remote server
set LOCAL_PATH_SERVER=C:\Users\jtking\Source\Repos\leftoverjacksons\CS-MINI_LISTEN\esp32_server\server.py
set LOCAL_PATH_TEMPLATE=C:\Users\jtking\Source\Repos\leftoverjacksons\CS-MINI_LISTEN\esp32_server\templates\form.html
set LOCAL_PATH_GRAPH=C:\Users\jtking\Source\Repos\leftoverjacksons\CS-MINI_LISTEN\esp32_server\templates\graph.html
set REMOTE_DIR=/home/engtech/Documents/wifi_testing_server
set REMOTE_IP=10.10.100.132

:: Use PuTTY's PLINK to check if the destination directory exists and create it if it doesn't
"C:\Program Files\PuTTY\plink.exe" -ssh engtech@%REMOTE_IP% -pw password2 "mkdir -p %REMOTE_DIR%/templates"
if errorlevel 1 (
    echo Failed to create directory.
    exit /b 1
)

:: Use PuTTY's PSCP to copy the files
"C:\Program Files\PuTTY\pscp.exe" -pw password2 "%LOCAL_PATH_SERVER%" engtech@%REMOTE_IP%:%REMOTE_DIR%/
if errorlevel 1 (
    echo Failed to copy server.py
    exit /b 1
)

"C:\Program Files\PuTTY\pscp.exe" -pw password2 "%LOCAL_PATH_TEMPLATE%" engtech@%REMOTE_IP%:%REMOTE_DIR%/templates/
if errorlevel 1 (
    echo Failed to copy form.html
    exit /b 1
)

"C:\Program Files\PuTTY\pscp.exe" -pw password2 "%LOCAL_PATH_GRAPH%" engtech@%REMOTE_IP%:%REMOTE_DIR%/templates/
if errorlevel 1 (
    echo Failed to copy graph.html
    exit /b 1
)

echo Deployment successful!
endlocal
