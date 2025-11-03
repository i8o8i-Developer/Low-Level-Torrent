"""
Blockchain Tracker Implementation
Decentralized Peer Discovery Using Blockchain
"""

import json
import hashlib
import time
from datetime import datetime
from typing import List, Optional, Dict
from loguru import logger

from Database import Blockchain_Record, Database_Manager


class Block:
    """Blockchain Block For Tracker Data"""
    
    def __init__(
        self,
        Block_Number: int,
        Previous_Hash: str,
        Data: dict,
        Timestamp: Optional[float] = None,
        Nonce: int = 0
    ):
        """
        Initialize Block
        
        Args:
            Block_Number: Block Index
            Previous_Hash: Hash Of Previous Block
            Data: Block Data (Peer/Torrent Info)
            Timestamp: Block Creation Time
            Nonce: Proof-Of-Work Nonce
        """
        self.Block_Number = Block_Number
        self.Previous_Hash = Previous_Hash
        self.Data = Data
        self.Timestamp = Timestamp or time.time()
        self.Nonce = Nonce
        self.Hash = self.Calculate_Hash()
    
    def Calculate_Hash(self) -> str:
        """Calculate Block Hash"""
        Block_String = json.dumps({
            'Block_Number': self.Block_Number,
            'Previous_Hash': self.Previous_Hash,
            'Data': self.Data,
            'Timestamp': self.Timestamp,
            'Nonce': self.Nonce
        }, sort_keys=True)
        
        return hashlib.sha256(Block_String.encode()).hexdigest()
    
    def Mine_Block(self, Difficulty: int = 4):
        """
        Mine Block With Proof-Of-Work
        
        Args:
            Difficulty: Number Of Leading Zeros Required
        """
        Target = '0' * Difficulty
        
        while self.Hash[:Difficulty] != Target:
            self.Nonce += 1
            self.Hash = self.Calculate_Hash()
        
        logger.info(f"Block #{self.Block_Number} Mined: {self.Hash}")
    
    def To_Dict(self) -> dict:
        """Convert Block To Dictionary"""
        return {
            'Block_Number': self.Block_Number,
            'Previous_Hash': self.Previous_Hash,
            'Data': self.Data,
            'Timestamp': self.Timestamp,
            'Nonce': self.Nonce,
            'Hash': self.Hash
        }


class Blockchain_Tracker:
    """Decentralized Blockchain-Based Tracker"""
    
    def __init__(self, DB_Manager: Database_Manager, Difficulty: int = 4):
        """
        Initialize Blockchain Tracker
        
        Args:
            DB_Manager: Database Manager
            Difficulty: Mining Difficulty
        """
        self.DB = DB_Manager
        self.Difficulty = Difficulty
        self.Chain: List[Block] = []
        
        # Initialize Or Load Chain
        self._Initialize_Chain()
        
        logger.info(f"Blockchain Tracker Initialized With {len(self.Chain)} Blocks")
    
    def _Initialize_Chain(self):
        """Initialize Or Load Blockchain From Database"""
        try:
            Session = self.DB.Get_Session()
            
            # Load Existing Blocks
            Records = Session.query(Blockchain_Record).order_by(Blockchain_Record.Block_Number).all()
            
            if Records:
                # Load From Database
                for Record in Records:
                    Data = json.loads(Record.Data.decode('utf-8'))
                    Block_Obj = Block(
                        Block_Number=Record.Block_Number,
                        Previous_Hash=Record.Previous_Hash,
                        Data=Data,
                        Timestamp=Record.Timestamp.timestamp(),
                        Nonce=Record.Nonce
                    )
                    self.Chain.append(Block_Obj)
                
                logger.info(f"Loaded {len(self.Chain)} Blocks From Database")
            else:
                # Create Genesis Block
                self._Create_Genesis_Block()
            
            Session.close()
            
        except Exception as E:
            logger.error(f"Failed To Initialize Chain: {E}")
            self._Create_Genesis_Block()
    
    def _Create_Genesis_Block(self):
        """Create Genesis Block"""
        try:
            Genesis = Block(
                Block_Number=0,
                Previous_Hash='0' * 64,
                Data={'Type': 'Genesis', 'Message': 'DST Blockchain Tracker Genesis Block'}
            )
            
            Genesis.Mine_Block(self.Difficulty)
            self.Chain.append(Genesis)
            
            # Save To Database
            self._Save_Block_To_DB(Genesis)
            
            logger.info("Genesis Block Created")
            
        except Exception as E:
            logger.error(f"Failed To Create Genesis Block: {E}")
            raise
    
    def _Save_Block_To_DB(self, Block_Obj: Block):
        """Save Block To Database"""
        try:
            Session = self.DB.Get_Session()
            
            Record = Blockchain_Record(
                Block_Hash=Block_Obj.Hash,
                Previous_Hash=Block_Obj.Previous_Hash,
                Block_Number=Block_Obj.Block_Number,
                Timestamp=datetime.fromtimestamp(Block_Obj.Timestamp),
                Data=json.dumps(Block_Obj.Data).encode('utf-8'),
                Nonce=Block_Obj.Nonce,
                Difficulty=self.Difficulty
            )
            
            Session.add(Record)
            Session.commit()
            Session.close()
            
        except Exception as E:
            logger.error(f"Failed To Save Block To Database: {E}")
            Session.close()
    
    def Get_Latest_Block(self) -> Block:
        """Get Latest Block In Chain"""
        return self.Chain[-1] if self.Chain else None
    
    def Add_Peer_Announcement(self, Peer_Info: dict) -> Block:
        """
        Add Peer Announcement To Blockchain
        
        Args:
            Peer_Info: Peer Information Dictionary
            
        Returns:
            New Block
        """
        try:
            Latest = self.Get_Latest_Block()
            
            New_Block = Block(
                Block_Number=Latest.Block_Number + 1,
                Previous_Hash=Latest.Hash,
                Data={
                    'Type': 'Peer_Announcement',
                    'Peer_Info': Peer_Info,
                    'Announced_At': datetime.utcnow().isoformat()
                }
            )
            
            # Mine Block
            New_Block.Mine_Block(self.Difficulty)
            
            # Add To Chain
            self.Chain.append(New_Block)
            
            # Save To Database
            self._Save_Block_To_DB(New_Block)
            
            logger.info(f"Added Peer Announcement Block #{New_Block.Block_Number}")
            return New_Block
            
        except Exception as E:
            logger.error(f"Failed To Add Peer Announcement: {E}")
            raise
    
    def Get_Peers_For_Torrent(self, Info_Hash: str) -> List[dict]:
        """
        Get Peers For Torrent From Blockchain
        
        Args:
            Info_Hash: Torrent Info Hash
            
        Returns:
            List Of Peer Information
        """
        try:
            Peers = []
            
            # Scan Blockchain For Relevant Peer Announcements
            for Block_Obj in reversed(self.Chain):
                if Block_Obj.Data.get('Type') == 'Peer_Announcement':
                    Peer_Info = Block_Obj.Data.get('Peer_Info', {})
                    
                    if Peer_Info.get('Info_Hash') == Info_Hash:
                        Peers.append(Peer_Info)
            
            logger.debug(f"Found {len(Peers)} Peers For {Info_Hash} In Blockchain")
            return Peers
            
        except Exception as E:
            logger.error(f"Failed To Get Peers From Blockchain: {E}")
            return []
    
    def Validate_Chain(self) -> bool:
        """Validate Entire Blockchain"""
        try:
            for I in range(1, len(self.Chain)):
                Current = self.Chain[I]
                Previous = self.Chain[I - 1]
                
                # Validate Hash
                if Current.Hash != Current.Calculate_Hash():
                    logger.error(f"Invalid Hash At Block #{Current.Block_Number}")
                    return False
                
                # Validate Link
                if Current.Previous_Hash != Previous.Hash:
                    logger.error(f"Broken Chain At Block #{Current.Block_Number}")
                    return False
                
                # Validate Proof-Of-Work
                if not Current.Hash.startswith('0' * self.Difficulty):
                    logger.error(f"Invalid PoW At Block #{Current.Block_Number}")
                    return False
            
            logger.info("Blockchain Validation Successful")
            return True
            
        except Exception as E:
            logger.error(f"Blockchain Validation Failed: {E}")
            return False


class Dead_Drop_Manager:
    """Anonymous File Exchange Via Dead Drops"""
    
    def __init__(self, DB_Manager: Database_Manager):
        """
        Initialize Dead Drop Manager
        
        Args:
            DB_Manager: Database Manager
        """
        self.DB = DB_Manager
        logger.info("Dead Drop Manager Initialized")
    
    def Create_Drop(
        self,
        Data: bytes,
        Encryption_Key: bytes,
        Expires_Hours: int = 48,
        Max_Access: int = 1
    ) -> str:
        """
        Create Anonymous Dead Drop
        
        Args:
            Data: Data To Store
            Encryption_Key: Encryption Key
            Expires_Hours: Expiration Time In Hours
            Max_Access: Maximum Access Count
            
        Returns:
            Drop ID
        """
        try:
            from Crypto import AES_Cipher
            from datetime import timedelta
            from Database import Dead_Drop
            
            # Encrypt Data
            AES = AES_Cipher(Encryption_Key)
            Nonce, Ciphertext = AES.Encrypt(Data)
            
            # Combine Nonce And Ciphertext
            Encrypted_Package = Nonce + Ciphertext
            
            # Generate Drop ID
            Drop_ID = hashlib.sha256(Encrypted_Package).hexdigest()
            
            # Calculate Key Hash
            Key_Hash = hashlib.sha256(Encryption_Key).hexdigest()
            
            # Create Expiration
            Expires_At = datetime.utcnow() + timedelta(hours=Expires_Hours)
            
            # Save To Database
            Session = self.DB.Get_Session()
            
            Drop = Dead_Drop(
                Id=Drop_ID,
                Encrypted_Data=Encrypted_Package,
                Encryption_Key_Hash=Key_Hash,
                Expires_At=Expires_At,
                Max_Access=Max_Access,
                Self_Destruct=True
            )
            
            Session.add(Drop)
            Session.commit()
            Session.close()
            
            logger.info(f"Dead Drop Created: {Drop_ID[:8]} (Expires In {Expires_Hours}h)")
            return Drop_ID
            
        except Exception as E:
            logger.error(f"Failed To Create Dead Drop: {E}")
            raise
    
    def Retrieve_Drop(self, Drop_ID: str, Encryption_Key: bytes) -> Optional[bytes]:
        """
        Retrieve Data From Dead Drop
        
        Args:
            Drop_ID: Drop Identifier
            Encryption_Key: Decryption Key
            
        Returns:
            Decrypted Data Or None
        """
        try:
            from Crypto import AES_Cipher
            from Database import Dead_Drop
            
            Session = self.DB.Get_Session()
            
            # Get Drop
            Drop = Session.query(Dead_Drop).filter_by(Id=Drop_ID).first()
            
            if not Drop:
                logger.warning(f"Dead Drop Not Found: {Drop_ID}")
                Session.close()
                return None
            
            # Check Expiration
            if datetime.utcnow() > Drop.Expires_At:
                logger.warning(f"Dead Drop Expired: {Drop_ID}")
                Session.delete(Drop)
                Session.commit()
                Session.close()
                return None
            
            # Verify Key
            Key_Hash = hashlib.sha256(Encryption_Key).hexdigest()
            if Key_Hash != Drop.Encryption_Key_Hash:
                logger.warning(f"Invalid Key For Dead Drop: {Drop_ID}")
                Session.close()
                return None
            
            # Decrypt Data
            Encrypted_Package = Drop.Encrypted_Data
            Nonce = Encrypted_Package[:12]
            Ciphertext = Encrypted_Package[12:]
            
            AES = AES_Cipher(Encryption_Key)
            Data = AES.Decrypt(Nonce, Ciphertext)
            
            # Update Access Count
            Drop.Access_Count += 1
            
            # Self-Destruct If Limit Reached
            if Drop.Self_Destruct and Drop.Access_Count >= Drop.Max_Access:
                logger.info(f"Dead Drop Self-Destructed: {Drop_ID}")
                Session.delete(Drop)
            
            Session.commit()
            Session.close()
            
            logger.info(f"Retrieved From Dead Drop: {Drop_ID[:8]}")
            return Data
            
        except Exception as E:
            logger.error(f"Failed To Retrieve From Dead Drop: {E}")
            return None
    
    def Cleanup_Expired(self):
        """Remove Expired Dead Drops"""
        try:
            from Database import Dead_Drop
            
            Session = self.DB.Get_Session()
            
            Expired = Session.query(Dead_Drop).filter(
                Dead_Drop.Expires_At < datetime.utcnow()
            ).all()
            
            for Drop in Expired:
                Session.delete(Drop)
            
            Session.commit()
            logger.info(f"Cleaned Up {len(Expired)} Expired Dead Drops")
            Session.close()
            
        except Exception as E:
            logger.error(f"Dead Drop Cleanup Failed: {E}")


if __name__ == "__main__":
    logger.add("Blockchain_Test.log")
    
    print("Testing Blockchain Tracker...")
    
    from Database import Initialize_Database
    
    # Initialize Database
    print("\n1. Initializing Database...")
    DB = Initialize_Database("sqlite:///Test_Blockchain.db")
    
    # Initialize Blockchain
    print("\n2. Creating Blockchain...")
    BC = Blockchain_Tracker(DB, Difficulty=2)
    print(f"✓ Blockchain Has {len(BC.Chain)} Blocks")
    
    # Add Peer
    print("\n3. Adding Peer Announcement...")
    BC.Add_Peer_Announcement({
        'Peer_Id': 'test_peer_123',
        'IP': '192.168.1.100',
        'Port': 6881,
        'Info_Hash': 'abc123'
    })
    print("✓ Peer Added To Blockchain")
    
    # Validate
    print("\n4. Validating Chain...")
    assert BC.Validate_Chain()
    print("✓ Blockchain Valid!")
    
    print("\n✓ All Blockchain Tests Passed!")
