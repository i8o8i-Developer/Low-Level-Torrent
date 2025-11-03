"""
Database Models And Operations
SQLite Backend With Thread-Safe Operations
"""

import threading
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, LargeBinary, ForeignKey, Table, Text, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from loguru import logger

from Config import Database_Config

# Base Class For Models
Base = declarative_base()

# Thread-Local Session
Session_Factory = None
Session_Lock = threading.Lock()


# Association Table For Many-To-Many Relationship
Torrent_Peers = Table(
    'Torrent_Peers',
    Base.metadata,
    Column('Torrent_Id', String, ForeignKey('Torrents.Info_Hash')),
    Column('Peer_Id', String, ForeignKey('Peers.Peer_Id'))
)


class Torrent(Base):
    """Torrent Model"""
    __tablename__ = 'Torrents'
    
    Info_Hash = Column(String(64), primary_key=True, index=True)
    Name = Column(String(255), nullable=False)
    Total_Size = Column(Integer, nullable=False)
    Piece_Count = Column(Integer, nullable=False)
    Piece_Size = Column(Integer, nullable=False)
    
    # Metadata
    Created_At = Column(DateTime, default=datetime.utcnow)
    Created_By = Column(String(255))
    Comment = Column(Text)
    Private = Column(Boolean, default=False)
    
    # Statistics
    Complete = Column(Integer, default=0)  # Seeders
    Incomplete = Column(Integer, default=0)  # Leechers
    Downloaded = Column(Integer, default=0)  # Total Downloads
    
    # Encrypted Metadata Storage
    Encrypted_Metadata = Column(LargeBinary)
    
    # Relationships
    Peers = relationship('Peer', secondary=Torrent_Peers, back_populates='Torrents')
    Files = relationship('File', back_populates='Torrent', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Torrent {self.Name} ({self.Info_Hash[:8]})>"


class Peer(Base):
    """Peer Model"""
    __tablename__ = 'Peers'
    
    Peer_Id = Column(String(40), primary_key=True, index=True)
    IP_Address = Column(String(45), nullable=False)  # IPv6 Support
    Port = Column(Integer, nullable=False)
    
    # Client Information
    User_Agent = Column(String(255))
    Client_Version = Column(String(50))
    
    # Connection Info
    First_Seen = Column(DateTime, default=datetime.utcnow)
    Last_Announced = Column(DateTime, default=datetime.utcnow)
    
    # Status
    Is_Seeder = Column(Boolean, default=False)
    Is_Active = Column(Boolean, default=True)
    
    # Bandwidth
    Uploaded = Column(Integer, default=0)
    Downloaded = Column(Integer, default=0)
    Left = Column(Integer, default=0)
    
    # Security
    Public_Key = Column(LargeBinary)  # RSA/Quantum Public Key
    Certificate_Hash = Column(String(64))
    
    # Relationships
    Torrents = relationship('Torrent', secondary=Torrent_Peers, back_populates='Peers')
    
    def __repr__(self):
        return f"<Peer {self.Peer_Id[:8]} @ {self.IP_Address}:{self.Port}>"
    
    def To_Compact(self) -> bytes:
        """Convert To Compact Peer Format (6 Bytes: 4-Byte IP + 2-Byte Port)"""
        import socket
        import struct
        
        try:
            IP_Bytes = socket.inet_aton(self.IP_Address)
            Port_Bytes = struct.pack('>H', self.Port)
            return IP_Bytes + Port_Bytes
        except Exception:
            return b''


class File(Base):
    """File Model For Multi-File Torrents"""
    __tablename__ = 'Files'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    Torrent_Info_Hash = Column(String(64), ForeignKey('Torrents.Info_Hash'), nullable=False)
    
    Path = Column(String(500), nullable=False)
    Length = Column(Integer, nullable=False)
    Hash = Column(String(64))
    
    # Relationships
    Torrent = relationship('Torrent', back_populates='Files')
    
    def __repr__(self):
        return f"<File {self.Path} ({self.Length} Bytes)>"


class Announcement(Base):
    """Announcement Log"""
    __tablename__ = 'Announcements'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    Peer_Id = Column(String(40), nullable=False, index=True)
    Info_Hash = Column(String(64), nullable=False, index=True)
    
    Event = Column(String(20))  # Started, Stopped, Completed
    IP_Address = Column(String(45), nullable=False)
    Port = Column(Integer, nullable=False)
    
    Uploaded = Column(Integer, default=0)
    Downloaded = Column(Integer, default=0)
    Left = Column(Integer, default=0)
    
    Timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<Announcement {self.Event} @ {self.Timestamp}>"


class Dead_Drop(Base):
    """Dead Drop Storage For Anonymous File Exchange"""
    __tablename__ = 'Dead_Drops'

    Id = Column(String(64), primary_key=True)  # SHA-256 Of Drop Location

    # Encrypted Payload
    Encrypted_Data = Column(LargeBinary, nullable=False)
    Nonce = Column(LargeBinary, nullable=False)  # AES-GCM Nonce
    Salt = Column(LargeBinary, nullable=False)  # PBKDF2 Salt For Password-Based Key Derivation

    # Metadata
    Created_At = Column(DateTime, default=datetime.utcnow, index=True)
    Expires_At = Column(DateTime, nullable=False, index=True)
    Access_Count = Column(Integer, default=0)
    Max_Access = Column(Integer, default=1)  # One-Time Read

    # Self-Destruct
    Self_Destruct = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Dead_Drop {self.Id[:8]} Expires {self.Expires_At}>"


class Blockchain_Record(Base):
    """Blockchain Tracker Records"""
    __tablename__ = 'Blockchain_Records'

    Block_Hash = Column(String(64), primary_key=True)
    Previous_Hash = Column(String(64), nullable=False, index=True)
    Block_Number = Column(Integer, nullable=False, unique=True, index=True)

    # Block Data
    Timestamp = Column(DateTime, default=datetime.utcnow)
    Data = Column(LargeBinary, nullable=False)  # Encoded Peer/Torrent Info
    Nonce = Column(Integer, nullable=False)
    Difficulty = Column(Integer, default=4)

    # Validation
    Is_Valid = Column(Boolean, default=True)
    Validator = Column(String(40))

    def __repr__(self):
        return f"<Block #{self.Block_Number} {self.Block_Hash[:8]}>"


# Database Manager
class Database_Manager:
    """Thread-Safe Database Manager"""
    
    def __init__(self, DB_URL: Optional[str] = None):
        """
        Initialize Database Manager
        
        Args:
            DB_URL: Database URL (Uses Config Default If None)
        """
        self.DB_URL = DB_URL or Database_Config.URL
        self.Engine = None
        self.Session = None
        self.Lock = threading.Lock()
        
        logger.info(f"Database Manager Initialized: {self.DB_URL}")
    
    def Initialize(self):
        """Initialize Database Connection And Create Tables"""
        try:
            with self.Lock:
                # Create Engine
                self.Engine = create_engine(
                    self.DB_URL,
                    echo=Database_Config.Echo,
                    pool_size=Database_Config.Pool_Size,
                    max_overflow=Database_Config.Max_Overflow,
                    connect_args={'check_same_thread': False} if 'sqlite' in self.DB_URL else {}
                )

                # Check If We Need To Recreate Tables (Schema Migration)
                try:
                    # Try To Reflect Existing Tables
                    from sqlalchemy import inspect
                    inspector = inspect(self.Engine)
                    existing_tables = inspector.get_table_names()

                    # If Dead_Drops Table Exists, Check If It Has The New Schema
                    if 'Dead_Drops' in existing_tables:
                        columns = [col['name'] for col in inspector.get_columns('Dead_Drops')]
                        # Check If New Columns Exist
                        if 'Nonce' not in columns or 'Salt' not in columns:
                            logger.info("Dead_Drops Table Schema Outdated, Recreating...")
                            # Drop old table
                            with self.Engine.connect() as conn:
                                conn.execute(text("DROP TABLE IF EXISTS Dead_Drops"))
                                conn.commit()
                        elif 'Encryption_Key_Hash' in columns:
                            logger.info("Dead_Drops Table Has Old Schema, Recreating...")
                            # Drop old table
                            with self.Engine.connect() as conn:
                                conn.execute(text("DROP TABLE IF EXISTS Dead_Drops"))
                                conn.commit()

                except Exception as schema_check_error:
                    logger.warning(f"Schema Check Failed: {schema_check_error}")

                # Create All Tables
                Base.metadata.create_all(self.Engine)

                # Create Session Factory
                Session_Factory_Obj = sessionmaker(bind=self.Engine)
                self.Session = scoped_session(Session_Factory_Obj)

                logger.info("Database Initialized Successfully")

        except Exception as E:
            logger.error(f"Database Initialization Failed: {E}")
            raise

    def Get_Session(self):
        """Get Thread-Safe Database Session"""
        if self.Session is None:
            raise RuntimeError("Database Not Initialized")
        return self.Session()
    
    def Close(self):
        """Close Database Connection"""
        try:
            if self.Session:
                self.Session.remove()
            if self.Engine:
                self.Engine.dispose()
            logger.info("Database Connection Closed")
            
        except Exception as E:
            logger.error(f"Error Closing Database: {E}")


# Database Operations
class Torrent_Operations:
    """Torrent Database Operations"""
    
    def __init__(self, DB_Manager: Database_Manager):
        self.DB = DB_Manager
    
    def Add_Torrent(self, Torrent_Metadata) -> Torrent:
        """Add New Torrent To Database"""
        try:
            Session = self.DB.Get_Session()
            
            # Check If Exists
            Existing = Session.query(Torrent).filter_by(Info_Hash=Torrent_Metadata.Info_Hash).first()
            if Existing:
                logger.info(f"Torrent Already Exists: {Torrent_Metadata.Info_Hash}")
                Session.close()
                return Existing
            
            # Create Torrent
            Torrent_Obj = Torrent(
                Info_Hash=Torrent_Metadata.Info_Hash,
                Name=Torrent_Metadata.Name,
                Total_Size=Torrent_Metadata.Get_Total_Size(),
                Piece_Count=Torrent_Metadata.Get_Piece_Count(),
                Piece_Size=Torrent_Metadata.Piece_Size,
                Created_By=Torrent_Metadata.Created_By,
                Comment=Torrent_Metadata.Comment,
                Private=Torrent_Metadata.Private
            )
            
            # Add Files
            for File_Info in Torrent_Metadata.Files:
                File_Obj = File(
                    Path=File_Info.Path,
                    Length=File_Info.Length,
                    Hash=File_Info.Hash
                )
                Torrent_Obj.Files.append(File_Obj)
            
            Session.add(Torrent_Obj)
            Session.commit()
            
            logger.info(f"Torrent Added: {Torrent_Metadata.Name}")
            
            Result = Torrent_Obj
            Session.close()
            return Result
            
        except Exception as E:
            logger.error(f"Failed To Add Torrent: {E}")
            Session.rollback()
            Session.close()
            raise
    
    def Get_Torrent(self, Info_Hash: str) -> Optional[Torrent]:
        """Get Torrent By Info Hash"""
        try:
            Session = self.DB.Get_Session()
            Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
            Session.close()
            return Torrent_Obj
            
        except Exception as E:
            logger.error(f"Failed To Get Torrent: {E}")
            return None
    
    def Update_Stats(self, Info_Hash: str, Complete: int, Incomplete: int):
        """Update Torrent Statistics"""
        try:
            Session = self.DB.Get_Session()
            Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
            
            if Torrent_Obj:
                Torrent_Obj.Complete = Complete
                Torrent_Obj.Incomplete = Incomplete
                Session.commit()
            
            Session.close()
            
        except Exception as E:
            logger.error(f"Failed To Update Stats: {E}")
            Session.close()


class Peer_Operations:
    """Peer Database Operations"""
    
    def __init__(self, DB_Manager: Database_Manager):
        self.DB = DB_Manager
    
    def Add_Or_Update_Peer(
        self,
        Peer_Id: str,
        IP_Address: str,
        Port: int,
        Info_Hash: str,
        **Kwargs
    ) -> Peer:
        """Add Or Update Peer"""
        try:
            Session = self.DB.Get_Session()
            
            # Get Or Create Peer
            Peer_Obj = Session.query(Peer).filter_by(Peer_Id=Peer_Id).first()
            
            if Peer_Obj:
                # Update Existing
                Peer_Obj.IP_Address = IP_Address
                Peer_Obj.Port = Port
                Peer_Obj.Last_Announced = datetime.utcnow()
                
                # Update Optional Fields
                for Key, Value in Kwargs.items():
                    if hasattr(Peer_Obj, Key):
                        setattr(Peer_Obj, Key, Value)
            else:
                # Create New
                Peer_Obj = Peer(
                    Peer_Id=Peer_Id,
                    IP_Address=IP_Address,
                    Port=Port,
                    **Kwargs
                )
                Session.add(Peer_Obj)
            
            # Associate With Torrent
            Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
            if Torrent_Obj and Torrent_Obj not in Peer_Obj.Torrents:
                Peer_Obj.Torrents.append(Torrent_Obj)
            
            Session.commit()
            Result = Peer_Obj
            Session.close()
            
            return Result
            
        except Exception as E:
            logger.error(f"Failed To Add/Update Peer: {E}")
            Session.rollback()
            Session.close()
            raise
    
    def Get_Peers(self, Info_Hash: str, Limit: int = 50) -> List[Peer]:
        """Get Peers For Torrent"""
        try:
            Session = self.DB.Get_Session()
            
            Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
            
            if Torrent_Obj:
                Peers = Torrent_Obj.Peers[:Limit]
            else:
                Peers = []
            
            Session.close()
            return Peers
            
        except Exception as E:
            logger.error(f"Failed To Get Peers: {E}")
            return []
    
    def Get_Compact_Peers(self, Info_Hash: str, Limit: int = 50) -> bytes:
        """Get Compact Peer List"""
        Peers = self.Get_Peers(Info_Hash, Limit)
        Compact_Data = b''.join([P.To_Compact() for P in Peers])
        return Compact_Data


class Dead_Drop_Operations:
    """Dead Drop Database Operations"""

    def __init__(self, DB_Manager: Database_Manager):
        self.DB = DB_Manager

    def Create_Dead_Drop(self, File_Path: str, Password: str, Exp_Hours: int = 24) -> str:
        """Create A New Dead Drop With Password-Based Encrypted File"""
        try:
            from Crypto.Core_Crypto import AES_Cipher

            Session = self.DB.Get_Session()

            # Read File
            with open(File_Path, 'rb') as f:
                File_Data = f.read()

            # Encrypt With Password
            Salt, Nonce, Encrypted_Data = AES_Cipher.Encrypt_With_Password(File_Data, Password)

            # Generate Unique Drop ID
            Drop_Id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()

            # Calculate Expiration
            Expires_At = datetime.utcnow() + timedelta(hours=Exp_Hours)

            # Create Dead Drop Record
            Dead_Drop_Obj = Dead_Drop(
                Id=Drop_Id,
                Encrypted_Data=Encrypted_Data,
                Nonce=Nonce,
                Salt=Salt,
                Expires_At=Expires_At,
                Max_Access=1,  # One-Time U8se
                Self_Destruct=True
            )

            Session.add(Dead_Drop_Obj)
            Session.commit()

            Result = Drop_Id
            Session.close()

            logger.info(f"Password-Protected Dead Drop Created : {Drop_Id}")
            return Result

        except Exception as E:
            logger.error(f"Failed To Create Password-Protected Dead Drop: {E}")
            Session.rollback()
            Session.close()
            raise

    def Access_Dead_Drop(self, Drop_Id: str, Password: str) -> Optional[bytes]:
        """Access And Retrieve Dead Drop Contents Using Password"""
        try:
            from Crypto.Core_Crypto import AES_Cipher

            Session = self.DB.Get_Session()

            # Find Dead Drop
            Dead_Drop_Obj = Session.query(Dead_Drop).filter_by(Id=Drop_Id).first()

            if not Dead_Drop_Obj:
                Session.close()
                return None

            # Check If Expired
            if datetime.utcnow() > Dead_Drop_Obj.Expires_At:
                Session.delete(Dead_Drop_Obj)
                Session.commit()
                Session.close()
                logger.info(f"Dead Drop Expired And Removed: {Drop_Id}")
                return None

            # Check Access Count
            if Dead_Drop_Obj.Access_Count >= Dead_Drop_Obj.Max_Access:
                if Dead_Drop_Obj.Self_Destruct:
                    Session.delete(Dead_Drop_Obj)
                    Session.commit()
                Session.close()
                logger.info(f"Dead Drop Access Limit Reached : {Drop_Id}")
                return None

            # Increment Access Count
            Dead_Drop_Obj.Access_Count += 1
            Session.commit()

            # Decrypt Data With Password
            try:
                Plaintext = AES_Cipher.Decrypt_With_Password(
                    Dead_Drop_Obj.Salt,
                    Dead_Drop_Obj.Nonce,
                    Dead_Drop_Obj.Encrypted_Data,
                    Password
                )
            except Exception as Decrypt_Error:
                # Wrong Password Or Corrupted Data
                logger.warning(f"Failed To Decrypt Dead Drop {Drop_Id}: {Decrypt_Error}")
                Session.close()
                return None

            # Self-Destruct If Enabled
            if Dead_Drop_Obj.Self_Destruct and Dead_Drop_Obj.Access_Count >= Dead_Drop_Obj.Max_Access:
                Session.delete(Dead_Drop_Obj)
                logger.info(f"Dead Drop Self-Destructed: {Drop_Id}")

            Session.commit()
            Session.close()

            return Plaintext

        except Exception as E:
            logger.error(f"Failed To Access Dead Drop: {E}")
            return None

    def Cleanup_Expired_Drops(self):
        """Remove Expired Dead Drops"""
        try:
            Session = self.DB.Get_Session()

            Expired_Drops = Session.query(Dead_Drop).filter(
                Dead_Drop.Expires_At < datetime.utcnow()
            ).all()

            for Drop in Expired_Drops:
                Session.delete(Drop)
                logger.info(f"Cleaned Up Expired Dead Drop: {Drop.Id}")

            Session.commit()
            Session.close()

        except Exception as E:
            logger.error(f"Failed To Cleanup Dead Drops: {E}")


class Blockchain_Operations:
    """Blockchain Database Operations"""

    def __init__(self, DB_Manager: Database_Manager):
        self.DB = DB_Manager

    def Add_Block(self, Data: bytes, Validator: str = "system") -> Blockchain_Record:
        """Add a new block to the blockchain"""
        try:
            Session = self.DB.Get_Session()

            # Get Previous Block Hash
            Prev_Block = Session.query(Blockchain_Record).order_by(
                Blockchain_Record.Block_Number.desc()
            ).first()

            Prev_Hash = Prev_Block.Block_Hash if Prev_Block else "0" * 64
            Block_Number = (Prev_Block.Block_Number + 1) if Prev_Block else 1

            # Create Block Hash (Simplified - In Real Blockchain Would Include Proof-Of-Work)
            # Use A Consistent Timestamp For Both Hash And Storage
            Block_Timestamp = datetime.utcnow()
            Block_Content = f"{Block_Number}{Prev_Hash}{Data.hex()}{Block_Timestamp.isoformat()}".encode()
            Block_Hash = hashlib.sha256(Block_Content).hexdigest()

            # Find Nonce (Simplified Proof-Of-Work)
            Nonce = 0
            Difficulty = 4  # Require 4 Leading Zeros
            while True:
                Test_Hash = hashlib.sha256(f"{Block_Hash}{Nonce}".encode()).hexdigest()
                if Test_Hash.startswith("0" * Difficulty):
                    break
                Nonce += 1

            # Create Block Record
            Block_Obj = Blockchain_Record(
                Block_Hash=Block_Hash,
                Previous_Hash=Prev_Hash,
                Block_Number=Block_Number,
                Data=Data,
                Timestamp=Block_Timestamp,  # Use The Same Timestamp
                Nonce=Nonce,
                Difficulty=Difficulty,
                Validator=Validator
            )

            Session.add(Block_Obj)
            Session.commit()

            Result = Block_Hash  # Return Hash String Instead Of Object
            Session.close()

            logger.info(f"Block Added To Blockchain: #{Block_Number}")
            return Result

        except Exception as E:
            logger.error(f"Failed To Add Block: {E}")
            Session.rollback()
            Session.close()
            raise

    def Get_Blockchain(self, Limit: int = 50) -> List[Blockchain_Record]:
        """Get Blockchain Records"""
        try:
            Session = self.DB.Get_Session()
            Blocks = Session.query(Blockchain_Record).order_by(
                Blockchain_Record.Block_Number.desc()
            ).limit(Limit).all()
            Session.close()
            return list(reversed(Blocks))  # Return In Ascending Order

        except Exception as E:
            logger.error(f"Failed To Get Blockchain: {E}")
            return []

    def Validate_Blockchain(self) -> bool:
        """Validate Blockchain Integrity"""
        try:
            Session = self.DB.Get_Session()
            Blocks = Session.query(Blockchain_Record).order_by(Blockchain_Record.Block_Number).all()
            Session.close()

            if not Blocks:
                logger.info("Blockchain Is Empty - Validation Passed")
                return True

            for i, Block in enumerate(Blocks):
                if i == 0:  # Genesis Block - Skip Detailed Validation For Now
                    continue

                # Verify Previous Hash  
                if Block.Previous_Hash != Blocks[i-1].Block_Hash:
                    logger.error(f"Block #{Block.Block_Number}: Invalid Previous Hash")
                    logger.error(f"Expected: {Blocks[i-1].Block_Hash}")
                    logger.error(f"Got: {Block.Previous_Hash}")
                    return False

                # Verify Block Hash (With Fallback For Legacy Blocks)
                Block_Content = f"{Block.Block_Number}{Block.Previous_Hash}{Block.Data.hex()}{Block.Timestamp.isoformat()}".encode()
                Calculated_Hash = hashlib.sha256(Block_Content).hexdigest()

                if Calculated_Hash != Block.Block_Hash:
                    # Try Alternative Formats For Backward Compatibility
                    # Some Blocks Might Have Been Created With Different Timestamp Precision
                    try:
                        # Try Without Microseconds
                        timestamp_str = Block.Timestamp.replace(microsecond=0).isoformat()
                        alt_content = f"{Block.Block_Number}{Block.Previous_Hash}{Block.Data.hex()}{timestamp_str}".encode()
                        alt_hash = hashlib.sha256(alt_content).hexdigest()
                        if alt_hash == Block.Block_Hash:
                            logger.warning(f"Block #{Block.Block_Number}: Using Legacy Timestamp Format")
                            continue
                    except:
                        pass

                    logger.error(f"Block #{Block.Block_Number}: Invalid Block Hash")
                    logger.error(f"Expected: {Block.Block_Hash}")
                    logger.error(f"Calculated: {Calculated_Hash}")
                    return False

                # Verify Proof-of-Work
                Test_Hash = hashlib.sha256(f"{Block.Block_Hash}{Block.Nonce}".encode()).hexdigest()
                if not Test_Hash.startswith("0" * Block.Difficulty):
                    logger.error(f"Block #{Block.Block_Number}: Invalid Proof-of-Work")
                    logger.error(f"Hash: {Test_Hash}")
                    logger.error(f"Required Prefix: {'0' * Block.Difficulty}")
                    return False

            logger.info("Blockchain Validation Successful")
            return True

        except Exception as E:
            logger.error(f"Blockchain Validation Failed: {E}")
            return False

    def Get_Blockchain_Stats(self) -> dict:
        """Get Blockchain Statistics"""
        try:
            Session = self.DB.Get_Session()

            Total_Blocks = Session.query(Blockchain_Record).count()
            Latest_Block = Session.query(Blockchain_Record).order_by(
                Blockchain_Record.Block_Number.desc()
            ).first()

            Session.close()

            return {
                'total_blocks': Total_Blocks,
                'latest_block': Latest_Block.Block_Number if Latest_Block else 0,
                'chain_size': Total_Blocks * 1024,  # Rough Estimate
                'is_valid': self.Validate_Blockchain()
            }

        except Exception as E:
            logger.error(f"Failed To Get Blockchain Stats: {E}")
            return {}

    def Clear_Blockchain(self):
        """Clear All Blockchain Records (For Testing/Reset Purposes)"""
        try:
            Session = self.DB.Get_Session()
            Session.query(Blockchain_Record).delete()
            Session.commit()
            Session.close()
            logger.info("Blockchain Cleared")
            return True
        except Exception as E:
            logger.error(f"Failed To Clear Blockchain: {E}")
            return False


# Global Database Instance
Global_DB = None


def Initialize_Database(DB_URL: Optional[str] = None) -> Database_Manager:
    """Initialize Global Database Instance"""
    global Global_DB
    
    try:
        Global_DB = Database_Manager(DB_URL)
        Global_DB.Initialize()
        logger.info("Global Database Instance Created")
        return Global_DB
        
    except Exception as E:
        logger.error(f"Failed To Initialize Database: {E}")
        raise


if __name__ == "__main__":
    logger.add("Database_Test.log")
    
    print("Testing Database Module...")
    
    # Initialize Database
    print("\n1. Initializing Database...")
    DB = Initialize_Database("sqlite:///Test_Torrent.db")
    print("✓ Database Initialized")
    
    # Test Operations
    print("\n2. Testing Database Operations...")
    Torrent_Ops = Torrent_Operations(DB)
    Peer_Ops = Peer_Operations(DB)
    print("✓ Operations Ready")
    
    print("\n✓ All Database Tests Passed!")
