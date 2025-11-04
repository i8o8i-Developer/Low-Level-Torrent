@ECHO OFF
REM DST TORRENT - ENHANCED LAUNCH SCRIPT
REM ACTIVATES ENVIRONMENT AND STARTS THE SERVER WITH VALIDATION
CHCP 65001 >nul
ECHO.
ECHO ================================================
ECHO    🚀 DST TORRENT - SERVER LAUNCH
ECHO    PRODUCTION-READY LOCALHOST DEPLOYMENT
ECHO ================================================
ECHO.

REM CHECK IF VIRTUAL ENVIRONMENT EXISTS
IF NOT EXIST ".venv" (
    ECHO ❌ [ERROR] VIRTUAL ENVIRONMENT NOT FOUND!
    ECHO 💡 PLEASE RUN Setup.bat FIRST TO CREATE THE ENVIRONMENT
    ECHO 🔧 Setup.bat Will Create The Virtual Environment And Install Dependencies
    ECHO.
    PAUSE
    EXIT /B 1
)

REM CHECK IF .env FILE EXISTS
IF NOT EXIST ".env" (
    ECHO ⚠️  [WARNING] .env CONFIGURATION FILE NOT FOUND!
    ECHO 📄 Creating Basic .env File...
    ECHO # DST Torrent Configuration > .env
    ECHO SERVER_HOST=127.0.0.1 >> .env
    ECHO SERVER_PORT=5043 >> .env
    ECHO DEBUG_MODE=false >> .env
    ECHO DATABASE_URL=sqlite:///Data/Torrent_System.db >> .env
    ECHO ✅ Basic .env File Created
    ECHO 💡 You Can Edit .env To Customize Settings
    ECHO.
)

REM CREATE REQUIRED DIRECTORIES IF MISSING
ECHO 📁 [STEP 1/6] ENSURING REQUIRED DIRECTORIES EXIST...
IF NOT EXIST "Data" mkdir Data
IF NOT EXIST "Logs" mkdir Logs
IF NOT EXIST "Storage\Torrents" mkdir Storage\Torrents
IF NOT EXIST "Storage\Temp" mkdir Storage\Temp
IF NOT EXIST "Storage\Uploads" mkdir Storage\Uploads
IF NOT EXIST "Crypto\Keys" mkdir Crypto\Keys
IF NOT EXIST "Downloads" mkdir Downloads
ECHO ✅ Directories Verified
ECHO.

ECHO 🔧 [STEP 2/6] ACTIVATING VIRTUAL ENVIRONMENT...
CALL .venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] FAILED TO ACTIVATE VIRTUAL ENVIRONMENT
    ECHO 💡 Try Running Setup.bat Again Or Check .venv Directory
    PAUSE
    EXIT /B 1
)
ECHO ✅ Virtual Environment Activated
ECHO.

ECHO 🔍 [STEP 3/6] VALIDATING SYSTEM REQUIREMENTS...
ECHO 🧪 Checking Python version...
FOR /F "tokens=2" %%i IN ('python --version 2^>^&1') DO SET PYTHON_VERSION=%%i
ECHO 📋 Python: %PYTHON_VERSION%

ECHO 🧪 Testing Core Dependencies...
python -c "import flask; print('✅ Flask OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

python -c "import flask_cors; print('✅ Flask-CORS OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask-CORS Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

python -c "import flask_sqlalchemy; print('✅ Flask-SQLAlchemy OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask-SQLAlchemy Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

python -c "import flask_limiter; print('✅ Flask-Limiter OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask-Limiter Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

python -c "import sqlalchemy; print('✅ SQLAlchemy OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] SQLAlchemy Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

python -c "import loguru; print('✅ Loguru OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Loguru Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

python -c "import psutil; print('✅ Psutil OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Psutil Not Installed
    ECHO 💡 Run Setup.bat To Install Missing Dependencies
    PAUSE
    EXIT /B 1
)

ECHO ✅ All Core Dependencies Validated Successfully
ECHO.

ECHO ⚙️  [STEP 4/6] VALIDATING CONFIGURATION...
python -c "import sys; sys.path.insert(0, '.'); from Config import Server_Config; print('✅ Server_Config loaded')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Server_Config Module Failed To Load
    ECHO 💡 Check Config/Settings.py And .env File
    PAUSE
    EXIT /B 1
)

python -c "import sys; sys.path.insert(0, '.'); from Config import Paths_Config; print('✅ Paths_Config loaded')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Paths_Config Module Failed To Load
    ECHO 💡 Check Config/Settings.py And Directory Permissions
    PAUSE
    EXIT /B 1
)

python -c "import sys; sys.path.insert(0, '.'); from Config import Paths_Config; Paths_Config.Create_All_Directories(); print('✅ Essential directories created')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Failed To Create Essential Directories
    ECHO 💡 Check Directory Permissions And Disk Space
    PAUSE
    EXIT /B 1
)

python -c "import sys; sys.path.insert(0, '.'); from Config import Server_Config; print(f'📋 Server will bind to: {Server_Config.Host}:{Server_Config.Port}')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Failed To Read Server Configuration
    ECHO 💡 Check .env File Settings
    PAUSE
    EXIT /B 1
)

python -c "import sys; sys.path.insert(0, '.'); from Config import Server_Config; print(f'📋 Debug mode: {Server_Config.Debug}')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Failed To Read Debug Configuration
    ECHO 💡 Check .env File Settings
    PAUSE
    EXIT /B 1
)

ECHO ✅ Configuration Validation Completed Successfully
ECHO.

ECHO 🔐 [STEP 5/6] CHECKING PORT AVAILABILITY...
netstat -ano | findstr :5043 >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    ECHO ⚠️  [WARNING] PORT 5043 IS ALREADY IN USE
    ECHO 💡 Either Stop The Other Service or Change SERVER_PORT In .env
    SET /P CONTINUE="🔄 CONTINUE ANYWAY? (Y/N): "
    IF /I NOT "%CONTINUE%"=="Y" (
        ECHO ❌ Launch Cancelled By User
        PAUSE
        EXIT /B 1
    )
) ELSE (
    ECHO ✅ Port 5043 Is Available
)
ECHO.

ECHO 🚀 [STEP 6/6] STARTING DST TORRENT SERVER...
ECHO.
ECHO ================================================
ECHO    🌐 SERVER INFORMATION
ECHO ================================================
ECHO 📡 SERVER URL: http://localhost:5043
ECHO 📡 SERVER URL: http://127.0.0.1:5043
ECHO 💚 HEALTH CHECK: http://localhost:5043/health
ECHO 📊 SYSTEM HEALTH: http://localhost:5043/system-health
ECHO 📁 LOGS: Logs\System.log
ECHO.
ECHO 🛑 PRESS CTRL+C TO STOP THE SERVER
ECHO ================================================
ECHO.

REM START THE SERVER WITH ERROR HANDLING
python Main_Server.py --host 127.0.0.1 --no-health-checks
SET SERVER_EXIT_CODE=%ERRORLEVEL%

REM SERVER HAS STOPPED
ECHO.
ECHO ================================================
ECHO    🛑 SERVER STOPPED
ECHO ================================================
IF %SERVER_EXIT_CODE% NEQ 0 (
    ECHO ❌ Server Exited With Error Code: %SERVER_EXIT_CODE%
    ECHO 💡 Check The Error Messages Above For Details
    ECHO 📋 Check Logs\System.log For More Information
) ELSE (
    ECHO ✅ Server Stopped Normally
)
ECHO.
PAUSE
