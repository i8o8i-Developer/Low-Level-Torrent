@ECHO OFF
REM DST TORRENT - ENHANCED SETUP SCRIPT
REM CREATES VIRTUAL ENVIRONMENT, INSTALLS DEPENDENCIES, AND SETS UP THE SYSTEM
CHCP 65001 >nul
ECHO.
ECHO ================================================
ECHO    🚀 DST TORRENT - ENHANCED SETUP
ECHO    COMPLETE SYSTEM INITIALIZATION
ECHO ================================================
ECHO.

REM CHECK IF PYTHON IS INSTALLED
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] PYTHON IS NOT INSTALLED OR NOT IN PATH
    ECHO 📥 PLEASE INSTALL PYTHON 3.11+ FROM https://www.python.org/
    ECHO 💡 Make Sure To Check "Add Python to PATH" During Installation
    PAUSE
    EXIT /B 1
)

ECHO ✅ [STEP 1/8] CHECKING PYTHON VERSION...
FOR /F "tokens=2" %%i IN ('python --version 2^>^&1') DO SET PYTHON_VERSION=%%i
ECHO 📋 Python Version: %PYTHON_VERSION%

REM CHECK PYTHON VERSION (MAJOR.MINOR)
FOR /F "tokens=1,2 delims=." %%a IN ("%PYTHON_VERSION%") DO (
    SET PYTHON_MAJOR=%%a
    SET PYTHON_MINOR=%%b
)
IF %PYTHON_MAJOR% LSS 3 (
    ECHO ❌ [ERROR] PYTHON 3.11+ REQUIRED. CURRENT: %PYTHON_VERSION%
    PAUSE
    EXIT /B 1
)
IF %PYTHON_MAJOR%==3 IF %PYTHON_MINOR% LSS 11 (
    ECHO ❌ [ERROR] PYTHON 3.11+ REQUIRED. CURRENT: %PYTHON_VERSION%
    PAUSE
    EXIT /B 1
)
ECHO ✅ Python Version Compatible
ECHO.

REM CHECK IF VENV ALREADY EXISTS
IF EXIST ".venv" (
    ECHO ⚠️  [WARNING] VIRTUAL ENVIRONMENT ALREADY EXISTS
    SET /P RECREATE="🔄 DO YOU WANT TO RECREATE IT? (Y/N): "
    IF /I "%RECREATE%"=="Y" (
        ECHO 🗑️  [STEP 2/8] REMOVING OLD VIRTUAL ENVIRONMENT...
        RMDIR /S /Q .venv 2>nul
        ECHO ✅ Old environment removed
    ) ELSE (
        ECHO ⏭️  KEEPING EXISTING ENVIRONMENT
        GOTO CREATE_DIRS
    )
)

ECHO 📦 [STEP 2/8] CREATING VIRTUAL ENVIRONMENT...
python -m venv .venv
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] FAILED TO CREATE VIRTUAL ENVIRONMENT
    ECHO 💡 Try Running As Administrator Or Check Disk Space
    PAUSE
    EXIT /B 1
)
ECHO ✅ Virtual Environment Created Successfully
ECHO.

:CREATE_DIRS
ECHO 📁 [STEP 3/8] CREATING REQUIRED DIRECTORIES...
IF NOT EXIST "Data" mkdir Data
IF NOT EXIST "Logs" mkdir Logs
IF NOT EXIST "Storage" mkdir Storage
IF NOT EXIST "Storage\Torrents" mkdir Storage\Torrents
IF NOT EXIST "Storage\Temp" mkdir Storage\Temp
IF NOT EXIST "Storage\Uploads" mkdir Storage\Uploads
IF NOT EXIST "Crypto" mkdir Crypto
IF NOT EXIST "Crypto\Keys" mkdir Crypto\Keys
IF NOT EXIST "Crypto\Certificates" mkdir Crypto\Certificates
IF NOT EXIST "Downloads" mkdir Downloads
IF NOT EXIST "Temp" mkdir Temp
ECHO ✅ All required directories created
ECHO.

ECHO ⚙️  [STEP 4/8] CREATING ENVIRONMENT CONFIGURATION...
IF NOT EXIST ".env" (
    ECHO 📄 Creating .env File From Template...
    COPY .env.example .env >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        ECHO ⚠️  [WARNING] Could Not copy .env.example, Creating Basic .env
        ECHO # DST Torrent Configuration > .env
        ECHO SERVER_HOST=127.0.0.1 >> .env
        ECHO SERVER_PORT=5043 >> .env
        ECHO DEBUG_MODE=false >> .env
        ECHO DATABASE_URL=sqlite:///Data/Torrent_System.db >> .env
    )
    ECHO ✅ .env File Created
) ELSE (
    ECHO ✅ .env File Already Exists
)
ECHO.

ECHO 🔧 [STEP 5/8] ACTIVATING VIRTUAL ENVIRONMENT...
CALL .venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] FAILED TO ACTIVATE VIRTUAL ENVIRONMENT
    PAUSE
    EXIT /B 1
)
ECHO ✅ Virtual Environment Activated
ECHO.

ECHO 📦 [STEP 6/8] UPGRADING PIP...
python -m pip install --upgrade pip
IF %ERRORLEVEL% NEQ 0 (
    ECHO ⚠️  [WARNING] FAILED TO UPGRADE PIP, CONTINUING...
)
ECHO.

ECHO 📦 [STEP 7/8] INSTALLING PROJECT DEPENDENCIES...
ECHO 📋 This May Take a Few Minutes...
pip install -r Requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] FAILED TO INSTALL DEPENDENCIES
    ECHO 💡 Check Your Internet Connection and Requirements.txt File
    ECHO 💡 Try: pip install --upgrade pip
    PAUSE
    EXIT /B 1
)
ECHO ✅ Dependencies Installed Successfully
ECHO.

ECHO 🔍 [STEP 8/8] VALIDATING SYSTEM SETUP...
ECHO 🧪 Testing Basic Imports...
python -c "import flask; print('✅ Flask OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask Not Installed
    ECHO 💡 Run: pip install flask
    PAUSE
    EXIT /B 1
)

python -c "import flask_cors; print('✅ Flask-CORS OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask-CORS Not Installed
    ECHO 💡 Run: pip install flask-cors
    PAUSE
    EXIT /B 1
)

python -c "import flask_sqlalchemy; print('✅ Flask-SQLAlchemy OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask-SQLAlchemy Not Installed
    ECHO 💡 Run: pip install flask-sqlalchemy
    PAUSE
    EXIT /B 1
)

python -c "import flask_limiter; print('✅ Flask-Limiter OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Flask-Limiter Not Installed
    ECHO 💡 Run: pip install flask-limiter
    PAUSE
    EXIT /B 1
)

python -c "import cryptography; print('✅ Cryptography OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Cryptography not installed
    ECHO 💡 Run: pip install cryptography
    PAUSE
    EXIT /B 1
)

python -c "import sqlalchemy; print('✅ SQLAlchemy OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] SQLAlchemy Not Installed
    ECHO 💡 Run: pip install sqlalchemy
    PAUSE
    EXIT /B 1
)

python -c "import loguru; print('✅ Loguru OK')" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ [ERROR] Loguru Not Installed
    ECHO 💡 Run: pip install loguru
    PAUSE
    EXIT /B 1
)

ECHO ✅ All Core Modules Validated Successfully
ECHO.

ECHO ================================================
ECHO    🎉 SETUP COMPLETED SUCCESSFULLY!
ECHO ================================================
ECHO.
ECHO 📍 VIRTUAL ENVIRONMENT: .venv
ECHO 🚀 TO START SERVER: Launch_Frontend.bat
ECHO 🔧 TO ACTIVATE MANUALLY: .venv\Scripts\activate.bat
ECHO 📁 CONFIG FILE: .env
ECHO 📋 LOGS: Logs\ directory
ECHO.
ECHO 💡 NEXT STEPS:
ECHO    1. Run Launch_Frontend.bat To Start The Server
ECHO    2. Open http://localhost:5043 In Your Browser
ECHO    3. Check Server Health At http://localhost:5043/health
ECHO.
PAUSE
