"""
Peer-To-Peer Communication Layer
Encrypted Peer Connections, Compact Peer Lists, Bandwidth Management
"""

import socket
import asyncio
import struct
from typing import Optional, List, Tuple
from datetime import datetime
from loguru import logger

from Config import Network_Config
from Crypto import Hybrid_Encryption, RSA_Handler


class Bandwidth_Manager:
    """Manages Upload And Download Bandwidth Limits"""
    
    def __init__(
        self,
        Upload_Limit: int = 0,
        Download_Limit: int = 0
    ):
        """
        Initialize Bandwidth Manager
        
        Args:
            Upload_Limit: Bytes Per Second (0 = Unlimited)
            Download_Limit: Bytes Per Second (0 = Unlimited)
        """
        self.Upload_Limit = Upload_Limit or Network_Config.Bandwidth_Limit_Upload
        self.Download_Limit = Download_Limit or Network_Config.Bandwidth_Limit_Download
        
        self.Uploaded_This_Second = 0
        self.Downloaded_This_Second = 0
        self.Last_Reset = datetime.utcnow()
        
        logger.info(f"Bandwidth Manager: Up={self.Upload_Limit} Down={self.Download_Limit} B/s")
    
    def Can_Upload(self, Bytes: int) -> bool:
        """Check If Upload Is Allowed"""
        self._Reset_If_Needed()
        
        if self.Upload_Limit == 0:
            return True
        
        return (self.Uploaded_This_Second + Bytes) <= self.Upload_Limit
    
    def Can_Download(self, Bytes: int) -> bool:
        """Check If Download Is Allowed"""
        self._Reset_If_Needed()
        
        if self.Download_Limit == 0:
            return True
        
        return (self.Downloaded_This_Second + Bytes) <= self.Download_Limit
    
    def Record_Upload(self, Bytes: int):
        """Record Uploaded Bytes"""
        self._Reset_If_Needed()
        self.Uploaded_This_Second += Bytes
    
    def Record_Download(self, Bytes: int):
        """Record Downloaded Bytes"""
        self._Reset_If_Needed()
        self.Downloaded_This_Second += Bytes
    
    def _Reset_If_Needed(self):
        """Reset Counters Every Second"""
        Now = datetime.utcnow()
        Elapsed = (Now - self.Last_Reset).total_seconds()
        
        if Elapsed >= 1.0:
            self.Uploaded_This_Second = 0
            self.Downloaded_This_Second = 0
            self.Last_Reset = Now


class Compact_Peer_List:
    """Handles Compact Peer List Format"""
    
    @staticmethod
    def Encode_Peers(Peers: List[Tuple[str, int]]) -> bytes:
        """
        Encode Peers To Compact Format
        
        Args:
            Peers: List Of (IP, Port) Tuples
            
        Returns:
            Compact Peer Data
        """
        try:
            Compact_Data = b''
            
            for IP, Port in Peers:
                # Convert IP To 4 Bytes
                IP_Bytes = socket.inet_aton(IP)
                
                # Convert Port To 2 Bytes (Big Endian)
                Port_Bytes = struct.pack('>H', Port)
                
                Compact_Data += IP_Bytes + Port_Bytes
            
            logger.debug(f"Encoded {len(Peers)} Peers To Compact Format")
            return Compact_Data
            
        except Exception as E:
            logger.error(f"Failed To Encode Compact Peers: {E}")
            return b''
    
    @staticmethod
    def Decode_Peers(Compact_Data: bytes) -> List[Tuple[str, int]]:
        """
        Decode Compact Peer List
        
        Args:
            Compact_Data: Compact Peer Data
            
        Returns:
            List Of (IP, Port) Tuples
        """
        try:
            Peers = []
            
            # Each Peer Is 6 Bytes (4 IP + 2 Port)
            for I in range(0, len(Compact_Data), 6):
                if I + 6 > len(Compact_Data):
                    break
                
                # Extract IP (4 Bytes)
                IP_Bytes = Compact_Data[I:I+4]
                IP = socket.inet_ntoa(IP_Bytes)
                
                # Extract Port (2 Bytes)
                Port_Bytes = Compact_Data[I+4:I+6]
                Port = struct.unpack('>H', Port_Bytes)[0]
                
                Peers.append((IP, Port))
            
            logger.debug(f"Decoded {len(Peers)} Peers From Compact Format")
            return Peers
            
        except Exception as E:
            logger.error(f"Failed To Decode Compact Peers: {E}")
            return []


class Peer_Connection:
    """Handles Individual Peer Connection"""
    
    def __init__(
        self,
        Peer_Id: str,
        IP: str,
        Port: int,
        Encryption_Handler: Optional[Hybrid_Encryption] = None
    ):
        """
        Initialize Peer Connection
        
        Args:
            Peer_Id: Peer Identifier
            IP: Peer IP Address
            Port: Peer Port
            Encryption_Handler: Hybrid Encryption Handler
        """
        self.Peer_Id = Peer_Id
        self.IP = IP
        self.Port = Port
        self.Encryption = Encryption_Handler
        
        self.Socket: Optional[socket.socket] = None
        self.Connected = False
        self.Choked = True
        self.Interested = False
        
        logger.info(f"Peer Connection Initialized: {Peer_Id} @ {IP}:{Port}")
    
    async def Connect(self, Timeout: int = Network_Config.Connection_Timeout) -> bool:
        """
        Connect To Peer
        
        Args:
            Timeout: Connection Timeout In Seconds
            
        Returns:
            Success Status
        """
        try:
            logger.info(f"Connecting To {self.IP}:{self.Port}...")
            
            # Create Socket
            self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.Socket.settimeout(Timeout)
            
            # Connect
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.Socket.connect,
                (self.IP, self.Port)
            )
            
            self.Connected = True
            logger.info(f"Connected To Peer {self.Peer_Id}")
            return True
            
        except Exception as E:
            logger.error(f"Failed To Connect To {self.IP}:{self.Port}: {E}")
            self.Connected = False
            return False
    
    async def Send_Handshake(self, handshake: bytes) -> bool:
        """
        Send BitTorrent Handshake (No Length Prefix)
        
        Args:
            handshake: Handshake Data (68 bytes)
            
        Returns:
            Success Status
        """
        try:
            if not self.Connected or not self.Socket:
                logger.warning("Cannot Send - Not Connected")
                return False
            
            # Send Raw Handshake (No Length Prefix)
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.Socket.sendall,
                handshake
            )
            
            logger.debug(f"Sent Handshake ({len(handshake)} Bytes) To {self.Peer_Id}")
            return True
            
        except Exception as E:
            logger.error(f"Failed To Send Handshake: {E}")
            return False
    
    async def Receive_Handshake(self) -> Optional[bytes]:
        """
        Receive BitTorrent Handshake (No Length Prefix)
        
        Returns:
            Handshake Data (80 bytes) Or None
        """
        try:
            if not self.Connected or not self.Socket:
                logger.warning("Cannot Receive - Not Connected")
                return None
            
            # Receive Exactly 80 Bytes For Handshake (SHA-256 version)
            handshake = await asyncio.get_event_loop().run_in_executor(
                None,
                self.Socket.recv,
                80
            )
            
            if len(handshake) != 80:
                logger.warning(f"Incomplete Handshake Received: {len(handshake)} Bytes")
                return None
            
            logger.debug(f"Received Handshake From {self.Peer_Id}")
            return handshake
            
        except Exception as E:
            logger.error(f"Failed To Receive Handshake: {E}")
            return None
    
    async def Send_Message(self, Message: bytes) -> bool:
        """
        Send Message To Peer
        
        Args:
            Message: Message Data
            
        Returns:
            Success Status
        """
        try:
            if not self.Connected or not self.Socket:
                logger.warning("Cannot Send - Not Connected")
                return False
            
            # Encrypt If Handler Available
            if self.Encryption:
                from Security import Global_Obfuscator
                if Global_Obfuscator:
                    Message = Global_Obfuscator.Obfuscate(Message, Method='dpi')
            
            # Send Message Length + Message
            Message_Length = len(Message)
            Length_Prefix = struct.pack('>I', Message_Length)
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.Socket.sendall,
                Length_Prefix + Message
            )
            
            logger.debug(f"Sent {Message_Length} Bytes To {self.Peer_Id}")
            return True
            
        except Exception as E:
            logger.error(f"Failed To Send Message: {E}")
            return False
    
    async def Receive_Message(self) -> Optional[bytes]:
        """
        Receive Message From Peer
        
        Returns:
            Message Data Or None
        """
        try:
            if not self.Connected or not self.Socket:
                logger.warning("Cannot Receive - Not Connected")
                return None
            
            # Receive Message Length
            Length_Data = await asyncio.get_event_loop().run_in_executor(
                None,
                self.Socket.recv,
                4
            )
            
            if not Length_Data:
                return None
            
            Message_Length = struct.unpack('>I', Length_Data)[0]
            
            # Receive Message
            Message = await asyncio.get_event_loop().run_in_executor(
                None,
                self.Socket.recv,
                Message_Length
            )
            
            # Decrypt If Necessary
            if self.Encryption:
                from Security import Global_Obfuscator
                if Global_Obfuscator:
                    Message = Global_Obfuscator.Deobfuscate(Message, Method='dpi')
            
            logger.debug(f"Received {len(Message)} Bytes From {self.Peer_Id}")
            return Message
            
        except Exception as E:
            logger.error(f"Failed To Receive Message: {E}")
            return None
    
    def Close(self):
        """Close Connection"""
        try:
            if self.Socket:
                self.Socket.close()
                self.Connected = False
                logger.info(f"Closed Connection To {self.Peer_Id}")
                
        except Exception as E:
            logger.error(f"Error Closing Connection: {E}")


class Peer_Manager:
    """Manages Multiple Peer Connections"""
    
    def __init__(
        self,
        Max_Connections: int = Network_Config.Max_Connections,
        Bandwidth_Manager_Instance: Optional[Bandwidth_Manager] = None
    ):
        """
        Initialize Peer Manager
        
        Args:
            Max_Connections: Maximum Concurrent Connections
            Bandwidth_Manager_Instance: Bandwidth Manager
        """
        self.Max_Connections = Max_Connections
        self.Bandwidth_Mgr = Bandwidth_Manager_Instance or Bandwidth_Manager()
        
        self.Peers: dict = {}  # Peer_Id -> Peer_Connection
        self.Active_Connections = 0
        
        logger.info(f"Peer Manager Initialized (Max Connections: {Max_Connections})")
    
    def Add_Peer(self, Peer_Connection: Peer_Connection):
        """Add Peer To Manager"""
        try:
            if len(self.Peers) >= self.Max_Connections:
                logger.warning("Max Connections Reached")
                return False
            
            self.Peers[Peer_Connection.Peer_Id] = Peer_Connection
            logger.info(f"Added Peer {Peer_Connection.Peer_Id}")
            return True
            
        except Exception as E:
            logger.error(f"Failed To Add Peer: {E}")
            return False
    
    def Remove_Peer(self, Peer_Id: str):
        """Remove Peer From Manager"""
        try:
            if Peer_Id in self.Peers:
                Peer = self.Peers[Peer_Id]
                Peer.Close()
                del self.Peers[Peer_Id]
                logger.info(f"Removed Peer {Peer_Id}")
                
        except Exception as E:
            logger.error(f"Failed To Remove Peer: {E}")
    
    def Get_Peer(self, Peer_Id: str) -> Optional[Peer_Connection]:
        """Get Peer Connection"""
        return self.Peers.get(Peer_Id)
    
    def Get_Connected_Peers(self) -> List[Peer_Connection]:
        """Get All Connected Peers"""
        return [P for P in self.Peers.values() if P.Connected]
    
    def Close_All(self):
        """Close All Peer Connections"""
        try:
            for Peer in self.Peers.values():
                Peer.Close()
            
            self.Peers.clear()
            logger.info("All Peer Connections Closed")
            
        except Exception as E:
            logger.error(f"Error Closing All Connections: {E}")


# Global Peer Manager
Global_Peer_Manager = None


def Initialize_Peer_System() -> dict:
    """Initialize Peer-To-Peer System"""
    global Global_Peer_Manager
    
    try:
        logger.info("Initializing P2P System...")
        
        Bandwidth_Mgr = Bandwidth_Manager()
        Global_Peer_Manager = Peer_Manager(Bandwidth_Manager_Instance=Bandwidth_Mgr)
        
        logger.info("P2P System Initialized Successfully")
        
        return {
            'Peer_Manager': Global_Peer_Manager,
            'Bandwidth_Manager': Bandwidth_Mgr
        }
        
    except Exception as E:
        logger.error(f"Failed To Initialize P2P System: {E}")
        raise


if __name__ == "__main__":
    logger.add("P2P_Test.log")
    
    print("Testing P2P Communication Layer...")
    
    # Test Compact Peers
    print("\n1. Testing Compact Peer List...")
    Test_Peers = [('192.168.1.1', 6881), ('192.168.1.2', 6882)]
    Compact = Compact_Peer_List.Encode_Peers(Test_Peers)
    Decoded = Compact_Peer_List.Decode_Peers(Compact)
    assert Test_Peers == Decoded
    print("✓ Compact Peer List Works!")
    
    # Test Bandwidth Manager
    print("\n2. Testing Bandwidth Manager...")
    BW = Bandwidth_Manager(Upload_Limit=1000, Download_Limit=1000)
    assert BW.Can_Upload(500)
    BW.Record_Upload(500)
    assert BW.Can_Upload(500)
    print("✓ Bandwidth Manager Works!")
    
    print("\n✓ All P2P Tests Passed!")
