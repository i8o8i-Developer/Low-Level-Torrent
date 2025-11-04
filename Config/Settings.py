"""
Configuration Settings For DST Torrent System
Production-Grade Settings With Environment Variable Support
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Server Configuration
class Server_Config:
    """Server Configuration Settings"""
    Host = os.getenv('SERVER_HOST', '0.0.0.0')
    Port = int(os.getenv('SERVER_PORT', 5043))
    Debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    Secret_Key = os.getenv('SECRET_KEY', os.urandom(32).hex())
    
# Database Configuration
class Database_Config:
    """Database Configuration Settings"""
    URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/Data/Torrent_System.db')
    Echo = False  # Set True For SQL Query Logging
    Pool_Size = 10
    Max_Overflow = 20
    
# Cryptography Configuration
class Crypto_Config:
    """Cryptography Settings"""
    # RSA Configuration
    RSA_Key_Size = 4096
    RSA_Private_Key_Path = BASE_DIR / os.getenv('RSA_PRIVATE_KEY_PATH', 'Crypto/Keys/Server_Private.pem')
    RSA_Public_Key_Path = BASE_DIR / os.getenv('RSA_PUBLIC_KEY_PATH', 'Crypto/Keys/Server_Public.pem')
    
    # AES Configuration
    AES_Key_Size = 256  # Bits
    AES_Master_Key = os.getenv('AES_MASTER_KEY', os.urandom(32).hex())
    
    # Quantum-Resistant Configuration
    Enable_Quantum_Resistance = os.getenv('ENABLE_QUANTUM_RESISTANCE', 'True').lower() == 'true'
    Quantum_Algorithm = 'Kyber1024'  # CRYSTALS-Kyber
    
    # Certificate Configuration
    Cert_Validity_Days = 365
    Cert_Path = BASE_DIR / 'Crypto/Certificates/'
    
# Blockchain Configuration
class Blockchain_Config:
    """Blockchain Tracker Settings"""
    Network = os.getenv('BLOCKCHAIN_NETWORK', 'TestNet')
    RPC_URL = os.getenv('BLOCKCHAIN_RPC_URL', 'http://localhost:8545')
    Contract_Address = os.getenv('CONTRACT_ADDRESS', None)
    Gas_Limit = 3000000
    
# Security Configuration
class Security_Config:
    """Advanced Security Features"""
    Enable_Encryption = os.getenv('ENABLE_ENCRYPTION', 'True').lower() == 'true'
    Enable_Steganography = os.getenv('ENABLE_STEGANOGRAPHY', 'False').lower() == 'true'
    Enable_Anti_DPI = True
    Enable_Zero_Knowledge = True
    
    # Self-Destruct Configuration
    Self_Destruct_Enabled = os.getenv('SELF_DESTRUCT_ENABLED', 'False').lower() == 'true'
    Self_Destruct_Hours = int(os.getenv('SELF_DESTRUCT_HOURS', 24))
    
    # Dead Drop Configuration
    Dead_Drop_Enabled = True
    Dead_Drop_Cleanup_Hours = 48
    
# Torrent Configuration
class Torrent_Config:
    """Torrent File And Piece Settings"""
    # File Extension
    Extension = '.dst'
    
    # Piece Size Configuration (In Bytes)
    Default_Piece_Size = int(os.getenv('DEFAULT_PIECE_SIZE', 262144))  # 256KB
    Max_Piece_Size = int(os.getenv('MAX_PIECE_SIZE', 2097152))  # 2MB
    Min_Piece_Size = int(os.getenv('MIN_PIECE_SIZE', 16384))  # 16KB
    
    # Hash Algorithm
    Hash_Algorithm = 'sha256'
    
    # Multi-File Support
    Max_Files_Per_Torrent = 10000
    
# Network Configuration
class Network_Config:
    """Network And P2P Settings"""
    Max_Connections = int(os.getenv('MAX_CONNECTIONS', 100))
    Connection_Timeout = int(os.getenv('CONNECTION_TIMEOUT', 30))
    
    # Bandwidth Management (Bytes Per Second, 0 = Unlimited)
    Bandwidth_Limit_Upload = int(os.getenv('BANDWIDTH_LIMIT_UP', 0))
    Bandwidth_Limit_Download = int(os.getenv('BANDWIDTH_LIMIT_DOWN', 0))
    
# Storage Configuration
class Storage_Config:
    """File Storage Settings"""
    Base_Directory = BASE_DIR / os.getenv('STORAGE_BASE_DIR', 'Storage')
    
    # Torrent Files Storage
    Torrents_Directory = Base_Directory / 'Torrents'
    Temp_Directory = Base_Directory / 'Temp'
    Uploads_Directory = Base_Directory / 'Uploads'
    
    # File Retention
    Temp_File_Cleanup_Hours = int(os.getenv('TEMP_CLEANUP_HOURS', 24))
    Max_Storage_Size_GB = int(os.getenv('MAX_STORAGE_SIZE_GB', 100))
    
    # File Permissions
    Directory_Permissions = 0o755
    File_Permissions = 0o644
    
# API Configuration
class API_Config:
    """API Settings"""
    Version = os.getenv('API_VERSION', 'v1')
    Rate_Limit_Requests = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    Rate_Limit_Window = int(os.getenv('RATE_LIMIT_WINDOW', 60))  # Seconds
    
    # CORS Settings
    CORS_Origins = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS_Methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_Headers = ['Content-Type', 'Authorization', 'X-API-Key']
    
    # Security Headers
    Security_Headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
# Monitoring Configuration
class Monitoring_Config:
    """Monitoring And Metrics Settings"""
    Enable_Metrics = os.getenv('ENABLE_METRICS', 'True').lower() == 'true'
    Metrics_Port = int(os.getenv('METRICS_PORT', 9090))
    
    # Health Check Settings
    Health_Check_Interval = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))
    Health_Check_Timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', 10))
    
    # Logging
    Log_Level = os.getenv('LOG_LEVEL', 'INFO')
    Log_Format = os.getenv('LOG_FORMAT', 'json')
    Log_Max_Size = os.getenv('LOG_MAX_SIZE', '10 MB')
    Log_Retention = os.getenv('LOG_RETENTION', '30 days')
    
# Paths Configuration (Legacy Support)
class Paths_Config:
    """Legacy Path Configuration"""
    Data_Directory = BASE_DIR / 'Data'
    Logs_Directory = BASE_DIR / 'Logs'
    Config_Directory = BASE_DIR / 'Config'
    
    # Peer Configuration
    Max_Peers_Per_Torrent = 50
    Peer_Timeout = 120
    
    # Compact Peer List
    Use_Compact_Peers = True
    
# Logging Configuration
class Logging_Config:
    """Logging Settings"""
    Level = os.getenv('LOG_LEVEL', 'INFO')
    File_Path = BASE_DIR / os.getenv('LOG_FILE_PATH', 'Logs/System.log')
    Max_File_Size = 10 * 1024 * 1024  # 10MB
    Backup_Count = 5
    Format = '{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}'
    
# Paths Configuration
class Paths_Config:
    """Directory Paths - Essential Only"""
    Data_Dir = BASE_DIR / 'Data'              # Database files
    Downloads_Dir = BASE_DIR / 'Downloads'    # Downloaded files
    Keys_Dir = BASE_DIR / 'Crypto/Keys'       # Encryption keys

    @classmethod
    def Create_All_Directories(cls):
        """Create Only Essential Directories"""
        essential_dirs = [
            cls.Data_Dir,
            cls.Downloads_Dir,
            cls.Keys_Dir
        ]

        for directory in essential_dirs:
            directory.mkdir(parents=True, exist_ok=True)

# Initialize Directories On Import
Paths_Config.Create_All_Directories()
