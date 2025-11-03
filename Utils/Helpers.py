"""
Utility Functions Module
Logging, Validation, And Helper Functions
"""

import re
import socket
from pathlib import Path
from typing import Optional
from loguru import logger

from Config import Logging_Config


def Initialize_Logging(Log_File: Optional[Path] = None):
    """
    Initialize Application Logging
    
    Args:
        Log_File: Log File Path (Uses Config Default If None)
    """
    try:
        Log_File = Log_File or Logging_Config.File_Path
        Log_File.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove Default Handler
        logger.remove()
        
        # Add Console Handler
        logger.add(
            sink=lambda msg: print(msg, end=''),
            format=Logging_Config.Format,
            level=Logging_Config.Level,
            colorize=True
        )
        
        # Add File Handler
        logger.add(
            sink=Log_File,
            format=Logging_Config.Format,
            level=Logging_Config.Level,
            rotation=Logging_Config.Max_File_Size,
            retention=Logging_Config.Backup_Count,
            compression="zip"
        )
        
        logger.info("Logging System Initialized")
        
    except Exception as E:
        print(f"Failed To Initialize Logging: {E}")
        raise


def Validate_Info_Hash(Info_Hash: str) -> bool:
    """
    Validate Info Hash Format
    
    Args:
        Info_Hash: Info Hash String
        
    Returns:
        True If Valid
    """
    if not Info_Hash:
        return False
    
    # Should Be 64 Character Hex String (SHA-256)
    if len(Info_Hash) != 64:
        return False
    
    if not re.match(r'^[a-fA-F0-9]{64}$', Info_Hash):
        return False
    
    return True


def Validate_Peer_Id(Peer_Id: str) -> bool:
    """
    Validate Peer ID
    
    Args:
        Peer_Id: Peer ID String
        
    Returns:
        True If Valid
    """
    if not Peer_Id:
        return False
    
    # Peer ID Should Be 20-40 Characters
    if len(Peer_Id) < 20 or len(Peer_Id) > 40:
        return False
    
    return True


def Validate_IP_Address(IP: str) -> bool:
    """
    Validate IP Address
    
    Args:
        IP: IP Address String
        
    Returns:
        True If Valid
    """
    try:
        socket.inet_aton(IP)
        return True
    except socket.error:
        return False


def Validate_Port(Port: int) -> bool:
    """
    Validate Port Number
    
    Args:
        Port: Port Number
        
    Returns:
        True If Valid
    """
    return 1 <= Port <= 65535


def Format_Bytes(Bytes: int) -> str:
    """
    Format Bytes To Human Readable String
    
    Args:
        Bytes: Number Of Bytes
        
    Returns:
        Formatted String
    """
    for Unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if Bytes < 1024.0:
            return f"{Bytes:.2f} {Unit}"
        Bytes /= 1024.0
    return f"{Bytes:.2f} PB"


def Sanitize_Filename(Filename: str) -> str:
    """
    Sanitize Filename For Safe Storage
    
    Args:
        Filename: Original Filename
        
    Returns:
        Sanitized Filename
    """
    # Remove Invalid Characters
    Invalid_Chars = r'[<>:"/\\|?*]'
    Sanitized = re.sub(Invalid_Chars, '_', Filename)
    
    # Trim Whitespace
    Sanitized = Sanitized.strip()
    
    # Limit Length
    if len(Sanitized) > 255:
        Sanitized = Sanitized[:255]
    
    return Sanitized


def Generate_Peer_Id(Client_Name: str = "DST", Version: str = "1.0") -> str:
    """
    Generate Unique Peer ID
    
    Args:
        Client_Name: Client Name
        Version: Client Version
        
    Returns:
        Peer ID String
    """
    import secrets
    
    # Format: -DS1000-<12 Random Characters>
    Prefix = f"-{Client_Name[:2].upper()}{Version.replace('.', '')[:4]}-"
    Random_Part = secrets.token_hex(6)
    
    Peer_Id = Prefix + Random_Part
    return Peer_Id


class Progress_Bar:
    """Simple Progress Bar For Console Output"""
    
    def __init__(self, Total: int, Width: int = 50, Prefix: str = "Progress"):
        """
        Initialize Progress Bar
        
        Args:
            Total: Total Number Of Items
            Width: Bar Width In Characters
            Prefix: Progress Bar Prefix
        """
        self.Total = Total
        self.Width = Width
        self.Prefix = Prefix
        self.Current = 0
    
    def Update(self, Current: int):
        """Update Progress Bar"""
        self.Current = Current
        
        Percent = (Current / self.Total) * 100
        Filled = int(self.Width * Current / self.Total)
        Bar = '█' * Filled + '-' * (self.Width - Filled)
        
        print(f'\r{self.Prefix}: |{Bar}| {Percent:.1f}%', end='', flush=True)
        
        if Current >= self.Total:
            print()  # New Line When Complete
    
    def Increment(self, Amount: int = 1):
        """Increment Progress"""
        self.Update(self.Current + Amount)


if __name__ == "__main__":
    print("Testing Utility Functions...")
    
    # Test Validation
    print("\n1. Testing Validation...")
    assert Validate_Info_Hash('a' * 64)
    assert not Validate_Info_Hash('invalid')
    assert Validate_Port(5043)
    assert not Validate_Port(70000)
    print("✓ Validation Works!")
    
    # Test Formatting
    print("\n2. Testing Formatting...")
    assert Format_Bytes(1024) == "1.00 KB"
    assert Format_Bytes(1048576) == "1.00 MB"
    print("✓ Formatting Works!")
    
    # Test Peer ID
    print("\n3. Testing Peer ID Generation...")
    Peer_Id = Generate_Peer_Id()
    print(f"Generated Peer ID: {Peer_Id}")
    assert len(Peer_Id) >= 20
    print("✓ Peer ID Generation Works!")
    
    print("\n✓ All Utility Tests Passed!")
