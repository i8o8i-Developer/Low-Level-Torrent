# Installation And Setup

This Guide Will Help You Get DST Torrent Up And Running On Your System.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Python Version**: Python 3.8 Or Higher
- **Memory**: Minimum 4GB RAM (8GB Recommended)
- **Storage**: 500MB Free Space For Installation + Space For Torrents
- **Network**: Stable Internet Connection

### Required Software
- **Python 3.8+**: [Download From Python.Org](https://python.org)
- **pip**: Python Package Installer (Included With Python 3.4+)
- **Git**: For Cloning The Repository (Optional)

## Installation Steps

### Step 1: Clone Or Download The Repository

#### Option A: Clone With Git (Recommended)
```bash
git clone https://github.com/i8o8i-Developer/Low-Level-Torrent.git
cd Low-Level-Torrent
```

#### Option B: Download ZIP
1. Go To [GitHub Repository](https://github.com/i8o8i-Developer/Low-Level-Torrent)
2. Click "Code" → "Download ZIP"
3. Extract The ZIP File To Your Desired Location
4. Open Terminal/Command Prompt And Navigate To The Extracted Folder

### Step 2: Install Python Dependencies

```bash
# Install Core Dependencies
pip install -r Requirements.txt
```

#### Optional Dependencies
```bash
# For Development And Testing
pip install -r Requirements-Dev.txt

# For Quantum-Resistant Cryptography (Requires liboqs)
pip install liboqs-python
```

### Step 3: Verify Installation

```bash
# Check Python Version
python --version

# Check If Core Modules Import Correctly
python -c "import sys; print('Python Path:', sys.executable)"
python -c "from Crypto import Initialize_Crypto_System; print('Crypto Module: OK')"
python -c "from Core import Create_Torrent_From_Path; print('Core Module: OK')"
```

### Step 4: Initial Configuration

#### Environment Variables (Optional)
Create A `.env` File In The Project Root:

```bash
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=5043
DEBUG_MODE=false

# Security Settings
ENABLE_ENCRYPTION=true
ENABLE_QUANTUM_RESISTANCE=true
ENABLE_ANTI_DPI=true

# Blockchain
BLOCKCHAIN_NETWORK=TestNet
```

#### Configuration Files
The System Uses Configuration Files Located In The `Config/` Directory:
- `Settings.py` - Main Configuration
- `Paths_Config.py` - Path Settings
- `Crypto_Config.py` - Cryptography Settings

## First Run Setup

### Start The Tracker Server

```bash
# Basic Startup
python Main_Server.py

# With Custom Port
SERVER_PORT=8080 python Main_Server.py

# With Debug Logging
DEBUG_MODE=true python Main_Server.py
```

### Create Your First Torrent

```bash
# Create A Sample Torrent For Testing
python Main_Client.py sample --output test_torrent.dst

# Create Torrent From A File
python Main_Client.py create --input /path/to/your/file.txt --output my_torrent.dst --tracker http://localhost:5043/announce

# Create Torrent From A Directory
python Main_Client.py create --input /path/to/directory --output my_directory_torrent.dst --tracker http://localhost:5043/announce
```

### Test Download And Seeding

```bash
# In Terminal 1: Start Seeding
python Main_Client.py seed --torrent test_torrent.dst

# In Terminal 2: Download The Torrent
python Main_Client.py download --torrent test_torrent.dst --output Downloads/
```

## Advanced Setup

### Firewall Configuration

DST Torrent Requires The Following Ports To Be Open:

- **5043** (Default): Tracker Server Port
- **6881-6889** (Optional): Peer Listening Ports (Auto-Selected If Available)

#### Windows Firewall
```powershell
# Allow Tracker Port
New-NetFirewallRule -DisplayName "DST Torrent Tracker" -Direction Inbound -Protocol TCP -LocalPort 5043 -Action Allow

# Allow Peer Ports (Range)
New-NetFirewallRule -DisplayName "DST Torrent Peers" -Direction Inbound -Protocol TCP -LocalPort 6881-6889 -Action Allow
```

#### Linux UFW
```bash
# Allow Tracker Port
sudo ufw allow 5043/tcp

# Allow Peer Ports
sudo ufw allow 6881:6889/tcp
```

### SSL/TLS Configuration

For Production Deployments, Configure SSL:

```bash
# Generate Self-Signed Certificate (Testing Only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Set Environment Variables
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
export ENABLE_SSL=true
```

### Database Setup

DST Torrent Uses SQLite By Default (No Setup Required). For Production:

```bash
# Use PostgreSQL (Advanced Users)
export DATABASE_URL=postgresql://user:password@localhost:5432/dst_torrent

# Or MySQL
export DATABASE_URL=mysql://user:password@localhost:3306/dst_torrent
```

## Troubleshooting Installation

### Common Issues

#### 1. Import Errors
```
ModuleNotFoundError: No module named 'cryptography'
```
**Solution**: Install Missing Dependencies
```bash
pip install --upgrade -r Requirements.txt
```

#### 2. Permission Errors
```
PermissionError: [Errno 13] Permission denied
```
**Solution**: Run With Appropriate Permissions Or Use Virtual Environment

#### 3. Port Already In Use
```
OSError: [Errno 48] Address already in use
```
**Solution**: Change Port Or Kill Process Using The Port
```bash
# Find Process Using Port 5043
netstat -tulpn | grep :5043
# Kill The Process
kill -9 <PID>
```

#### 4. Quantum Crypto Not Available
```
WARNING: liboqs Not Available - Quantum-Resistant Crypto Disabled
```
**Solution**: Install liboqs (Optional)
```bash
# On Ubuntu/Debian
sudo apt-get install liboqs-dev
pip install liboqs-python

# On macOS
brew install liboqs
pip install liboqs-python
```

### Virtual Environment Setup

For Isolated Installation:

```bash
# Create Virtual Environment
python -m venv dst_env

# Activate Environment
# Windows
dst_env\Scripts\activate
# Linux/macOS
source dst_env/bin/activate

# Install Dependencies
pip install -r Requirements.txt

# Deactivate When Done
deactivate
```