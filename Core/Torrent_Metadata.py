"""
Torrent Metadata And File Handler Module
Implements .dst File Format, SHA-256 Hashing, Multi-File Support
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime
import bencodepy
from loguru import logger

from Config import Torrent_Config, Crypto_Config
from Crypto import Hash_Functions, Hybrid_Encryption, RSA_Handler


class Piece_Manager:
    """Manages Torrent Pieces And Hashing"""
    
    def __init__(self, Piece_Size: int = Torrent_Config.Default_Piece_Size):
        """
        Initialize Piece Manager
        
        Args:
            Piece_Size: Size Of Each Piece In Bytes
        """
        if Piece_Size < Torrent_Config.Min_Piece_Size or Piece_Size > Torrent_Config.Max_Piece_Size:
            raise ValueError(f"Piece Size Must Be Between {Torrent_Config.Min_Piece_Size} And {Torrent_Config.Max_Piece_Size}")
        
        self.Piece_Size = Piece_Size
        self.Pieces = []
        logger.info(f"Piece Manager Initialized With Piece Size: {Piece_Size} Bytes")
    
    def Calculate_Pieces(self, File_Path: Path) -> List[str]:
        """
        Calculate SHA-256 Hashes For All Pieces Of A File
        
        Args:
            File_Path: Path To File
            
        Returns:
            List Of Piece Hashes
        """
        try:
            Piece_Hashes = []
            
            with open(File_Path, 'rb') as F:
                Piece_Number = 0
                
                while True:
                    Piece_Data = F.read(self.Piece_Size)
                    if not Piece_Data:
                        break
                    
                    # Calculate SHA-256 Hash
                    Piece_Hash = Hash_Functions.SHA256(Piece_Data)
                    Piece_Hashes.append(Piece_Hash)
                    
                    Piece_Number += 1
                    
                    if Piece_Number % 100 == 0:
                        logger.debug(f"Processed {Piece_Number} Pieces...")
            
            logger.info(f"Calculated {len(Piece_Hashes)} Piece Hashes For {File_Path.name}")
            return Piece_Hashes
            
        except Exception as E:
            logger.error(f"Failed To Calculate Pieces For {File_Path}: {E}")
            raise
    
    def Calculate_Multi_File_Pieces(self, File_Paths: List[Path]) -> List[str]:
        """
        Calculate Pieces For Multiple Files (Concatenated)
        
        Args:
            File_Paths: List Of File Paths
            
        Returns:
            List Of Piece Hashes
        """
        try:
            Piece_Hashes = []
            Current_Piece = b''
            
            for File_Path in File_Paths:
                with open(File_Path, 'rb') as F:
                    while True:
                        # Read Remaining Space In Current Piece
                        Bytes_Needed = self.Piece_Size - len(Current_Piece)
                        Chunk = F.read(Bytes_Needed)
                        
                        if not Chunk:
                            break
                        
                        Current_Piece += Chunk
                        
                        # If Piece Is Complete, Hash It
                        if len(Current_Piece) == self.Piece_Size:
                            Piece_Hash = Hash_Functions.SHA256(Current_Piece)
                            Piece_Hashes.append(Piece_Hash)
                            Current_Piece = b''
            
            # Hash Remaining Data
            if Current_Piece:
                Piece_Hash = Hash_Functions.SHA256(Current_Piece)
                Piece_Hashes.append(Piece_Hash)
            
            logger.info(f"Calculated {len(Piece_Hashes)} Piece Hashes For {len(File_Paths)} Files")
            return Piece_Hashes
            
        except Exception as E:
            logger.error(f"Failed To Calculate Multi-File Pieces: {E}")
            raise
    
    def Verify_Piece(self, Piece_Data: bytes, Expected_Hash: str) -> bool:
        """
        Verify Piece Data Against Expected Hash
        
        Args:
            Piece_Data: Piece Data To Verify
            Expected_Hash: Expected SHA-256 Hash
            
        Returns:
            True If Valid
        """
        try:
            Actual_Hash = Hash_Functions.SHA256(Piece_Data)
            Is_Valid = Actual_Hash == Expected_Hash
            
            if not Is_Valid:
                logger.warning(f"Piece Verification Failed: Expected {Expected_Hash}, Got {Actual_Hash}")
            
            return Is_Valid
            
        except Exception as E:
            logger.error(f"Piece Verification Error: {E}")
            return False


class File_Info:
    """Represents A Single File In The Torrent"""
    
    def __init__(self, Path: str, Length: int, Hash: Optional[str] = None):
        """
        Initialize File Information
        
        Args:
            Path: Relative File Path
            Length: File Size In Bytes
            Hash: SHA-256 Hash Of Complete File
        """
        self.Path = Path
        self.Length = Length
        self.Hash = Hash
    
    def To_Dict(self) -> dict:
        """Convert To Dictionary"""
        return {
            'Path': self.Path,
            'Length': self.Length,
            'Hash': self.Hash
        }
    
    @classmethod
    def From_Dict(cls, Data: dict) -> 'File_Info':
        """Create From Dictionary"""
        return cls(
            Path=Data['Path'],
            Length=Data['Length'],
            Hash=Data.get('Hash')
        )


class Torrent_Metadata:
    """
    DST Torrent Metadata Structure
    Implements Custom .dst Format With Enhanced Security
    """
    
    def __init__(
        self,
        Name: str,
        Files: List[File_Info],
        Piece_Size: int,
        Piece_Hashes: List[str],
        Tracker_URLs: Optional[List[str]] = None,
        Comment: Optional[str] = None,
        Created_By: Optional[str] = None,
        Private: bool = False
    ):
        """
        Initialize Torrent Metadata
        
        Args:
            Name: Torrent Name
            Files: List Of Files
            Piece_Size: Size Of Each Piece
            Piece_Hashes: List Of SHA-256 Piece Hashes
            Tracker_URLs: List Of Tracker URLs
            Comment: Optional Comment
            Created_By: Creator Information
            Private: Private Torrent Flag
        """
        self.Name = Name
        self.Files = Files
        self.Piece_Size = Piece_Size
        self.Piece_Hashes = Piece_Hashes
        self.Tracker_URLs = Tracker_URLs or []
        self.Comment = Comment
        self.Created_By = Created_By or "DST Torrent System v1.0"
        self.Private = Private
        self.Creation_Date = int(datetime.utcnow().timestamp())
        
        # Calculate Info Hash
        self.Info_Hash = self._Calculate_Info_Hash()
        
        logger.info(f"Torrent Metadata Created: {Name} ({len(Files)} Files, {len(Piece_Hashes)} Pieces)")
    
    def _Calculate_Info_Hash(self) -> str:
        """Calculate SHA-256 Info Hash"""
        Info_Dict = {
            'Name': self.Name,
            'Piece_Size': self.Piece_Size,
            'Piece_Hashes': self.Piece_Hashes,
            'Files': [F.To_Dict() for F in self.Files]
        }
        
        Info_Json = json.dumps(Info_Dict, sort_keys=True)
        return Hash_Functions.SHA256(Info_Json.encode('utf-8'))
    
    def To_Dict(self) -> dict:
        """Convert Metadata To Dictionary"""
        return {
            'Name': self.Name,
            'Files': [F.To_Dict() for F in self.Files],
            'Piece_Size': self.Piece_Size,
            'Piece_Hashes': self.Piece_Hashes,
            'Tracker_URLs': self.Tracker_URLs,
            'Comment': self.Comment,
            'Created_By': self.Created_By,
            'Private': self.Private,
            'Creation_Date': self.Creation_Date,
            'Info_Hash': self.Info_Hash,
            'DST_Version': '1.0'
        }
    
    @classmethod
    def From_Dict(cls, Data: dict) -> 'Torrent_Metadata':
        """Create Metadata From Dictionary"""
        Files = [File_Info.From_Dict(F) for F in Data['Files']]
        
        Metadata = cls(
            Name=Data['Name'],
            Files=Files,
            Piece_Size=Data['Piece_Size'],
            Piece_Hashes=Data['Piece_Hashes'],
            Tracker_URLs=Data.get('Tracker_URLs', []),
            Comment=Data.get('Comment'),
            Created_By=Data.get('Created_By'),
            Private=Data.get('Private', False)
        )
        
        Metadata.Creation_Date = Data.get('Creation_Date', Metadata.Creation_Date)
        return Metadata
    
    def Get_Total_Size(self) -> int:
        """Get Total Size Of All Files"""
        return sum(F.Length for F in self.Files)
    
    def Get_Piece_Count(self) -> int:
        """Get Total Number Of Pieces"""
        return len(self.Piece_Hashes)


class DST_File_Handler:
    """
    Handles .dst Torrent File Creation And Loading
    With AES-256-GCM Encryption And RSA Signatures
    """
    
    def __init__(self, RSA_Handler_Instance: Optional[RSA_Handler] = None):
        """
        Initialize DST File Handler
        
        Args:
            RSA_Handler_Instance: RSA Handler For Signing (Optional)
        """
        self.RSA = RSA_Handler_Instance
        if self.RSA:
            self.Hybrid_Crypto = Hybrid_Encryption(self.RSA)
        else:
            self.Hybrid_Crypto = None
        
        logger.info("DST File Handler Initialized")
    
    def Create_Torrent(
        self,
        Input_Path: Path,
        Output_Path: Path,
        Tracker_URLs: List[str],
        Piece_Size: Optional[int] = None,
        Comment: Optional[str] = None,
        Private: bool = False,
        Encrypt: bool = True
    ) -> Torrent_Metadata:
        """
        Create A New .dst Torrent File
        
        Args:
            Input_Path: Path To File Or Directory
            Output_Path: Output .dst File Path
            Tracker_URLs: List Of Tracker URLs
            Piece_Size: Custom Piece Size (Optional)
            Comment: Torrent Comment
            Private: Private Torrent Flag
            Encrypt: Enable Encryption
            
        Returns:
            Torrent Metadata
        """
        try:
            logger.info(f"Creating Torrent From {Input_Path}...")
            
            # Validate Input
            if not Input_Path.exists():
                raise FileNotFoundError(f"Input Path Does Not Exist: {Input_Path}")
            
            # Determine Piece Size
            if Piece_Size is None:
                Piece_Size = Torrent_Config.Default_Piece_Size
            
            Piece_Mgr = Piece_Manager(Piece_Size)
            
            # Collect Files
            if Input_Path.is_file():
                Files = [Input_Path]
                Torrent_Name = Input_Path.name
            else:
                Files = sorted(Input_Path.rglob('*'))
                Files = [F for F in Files if F.is_file()]
                Torrent_Name = Input_Path.name
            
            if not Files:
                raise ValueError("No Files Found To Create Torrent")
            
            logger.info(f"Found {len(Files)} Files")
            
            # Calculate File Information
            File_Infos = []
            for File_Path in Files:
                Relative_Path = str(File_Path.relative_to(Input_Path.parent))
                File_Hash = Hash_Functions.SHA256_File(File_Path)
                File_Size = File_Path.stat().st_size
                
                File_Info_Obj = File_Info(Relative_Path, File_Size, File_Hash)
                File_Infos.append(File_Info_Obj)
            
            # Calculate Pieces
            logger.info("Calculating Piece Hashes...")
            if len(Files) == 1:
                Piece_Hashes = Piece_Mgr.Calculate_Pieces(Files[0])
            else:
                Piece_Hashes = Piece_Mgr.Calculate_Multi_File_Pieces(Files)
            
            # Create Metadata
            Metadata = Torrent_Metadata(
                Name=Torrent_Name,
                Files=File_Infos,
                Piece_Size=Piece_Size,
                Piece_Hashes=Piece_Hashes,
                Tracker_URLs=Tracker_URLs,
                Comment=Comment,
                Private=Private
            )
            
            # Save To File
            self.Save_Torrent(Metadata, Output_Path, Encrypt)
            
            logger.info(f"Torrent Created Successfully: {Output_Path}")
            return Metadata
            
        except Exception as E:
            logger.error(f"Failed To Create Torrent: {E}")
            raise
    
    def Save_Torrent(self, Metadata: Torrent_Metadata, File_Path: Path, Encrypt: bool = True):
        """
        Save Torrent Metadata To .dst File
        
        Args:
            Metadata: Torrent Metadata
            File_Path: Output File Path
            Encrypt: Enable Encryption
        """
        try:
            # Convert To JSON
            Metadata_Dict = Metadata.To_Dict()
            Metadata_Json = json.dumps(Metadata_Dict, indent=2)
            Metadata_Bytes = Metadata_Json.encode('utf-8')
            
            # Sign Metadata
            Signature = None
            if self.RSA and self.RSA.Private_Key:
                Signature = self.RSA.Sign(Metadata_Bytes)
                logger.debug("Metadata Signed With RSA")
            
            # Encrypt If Requested
            if Encrypt and self.Hybrid_Crypto:
                Encrypted_Package = self.Hybrid_Crypto.Encrypt(Metadata_Bytes)
                
                # Create Encrypted Container
                Container = {
                    'Encrypted': True,
                    'Data': {
                        'Encrypted_Session_Key': Encrypted_Package['Encrypted_Session_Key'].hex(),
                        'Nonce': Encrypted_Package['Nonce'].hex(),
                        'Ciphertext': Encrypted_Package['Ciphertext'].hex()
                    },
                    'Signature': Signature.hex() if Signature else None
                }
                
                logger.debug("Metadata Encrypted With Hybrid Encryption")
            else:
                # Unencrypted Container
                Container = {
                    'Encrypted': False,
                    'Data': Metadata_Json,
                    'Signature': Signature.hex() if Signature else None
                }
            
            # Add DST Header
            DST_File = {
                'DST_Magic': 'DST_TORRENT_V1',
                'Container': Container
            }
            
            # Write To File
            File_Path.parent.mkdir(parents=True, exist_ok=True)
            with open(File_Path, 'w', encoding='utf-8') as F:
                json.dump(DST_File, F, indent=2)
            
            logger.info(f"Torrent Saved To {File_Path}")
            
        except Exception as E:
            logger.error(f"Failed To Save Torrent: {E}")
            raise
    
    def Load_Torrent(self, File_Path: Path, Verify_Signature: bool = True) -> Torrent_Metadata:
        """
        Load Torrent Metadata From .dst File
        
        Args:
            File_Path: .dst File Path
            Verify_Signature: Verify RSA Signature
            
        Returns:
            Torrent Metadata
        """
        try:
            logger.info(f"Loading Torrent From {File_Path}...")
            
            # Read File
            with open(File_Path, 'r', encoding='utf-8') as F:
                DST_File = json.load(F)
            
            # Validate Magic
            if DST_File.get('DST_Magic') != 'DST_TORRENT_V1':
                raise ValueError("Invalid DST File Format")
            
            Container = DST_File['Container']
            Is_Encrypted = Container.get('Encrypted', False)
            Signature_Hex = Container.get('Signature')
            
            # Decrypt If Necessary
            if Is_Encrypted:
                if not self.Hybrid_Crypto:
                    raise ValueError("Cannot Decrypt - No Encryption Handler Provided")
                
                Data = Container['Data']
                Encrypted_Package = {
                    'Encrypted_Session_Key': bytes.fromhex(Data['Encrypted_Session_Key']),
                    'Nonce': bytes.fromhex(Data['Nonce']),
                    'Ciphertext': bytes.fromhex(Data['Ciphertext'])
                }
                
                Metadata_Bytes = self.Hybrid_Crypto.Decrypt(Encrypted_Package)
                Metadata_Json = Metadata_Bytes.decode('utf-8')
                
                logger.debug("Metadata Decrypted Successfully")
            else:
                Metadata_Json = Container['Data']
                Metadata_Bytes = Metadata_Json.encode('utf-8')
            
            # Verify Signature
            if Verify_Signature and Signature_Hex and self.RSA:
                Signature = bytes.fromhex(Signature_Hex)
                if not self.RSA.Verify(Metadata_Bytes, Signature):
                    logger.warning("Signature Verification Failed!")
                else:
                    logger.debug("Signature Verified Successfully")
            
            # Parse Metadata
            Metadata_Dict = json.loads(Metadata_Json)
            Metadata = Torrent_Metadata.From_Dict(Metadata_Dict)
            
            logger.info(f"Torrent Loaded: {Metadata.Name}")
            return Metadata
            
        except Exception as E:
            logger.error(f"Failed To Load Torrent: {E}")
            raise


# Utility Functions
def Create_Torrent_From_Path(
    Input_Path: Union[str, Path],
    Output_Path: Union[str, Path],
    Tracker_URLs: List[str],
    **Kwargs
) -> Torrent_Metadata:
    """
    Convenience Function To Create Torrent
    
    Args:
        Input_Path: File Or Directory Path
        Output_Path: Output .dst File Path
        Tracker_URLs: Tracker URLs
        **Kwargs: Additional Options
        
    Returns:
        Torrent Metadata
    """
    Input_Path = Path(Input_Path)
    Output_Path = Path(Output_Path)
    
    # Ensure .dst Extension
    if not Output_Path.suffix == Torrent_Config.Extension:
        Output_Path = Output_Path.with_suffix(Torrent_Config.Extension)
    
    Handler = DST_File_Handler()
    return Handler.Create_Torrent(Input_Path, Output_Path, Tracker_URLs, **Kwargs)


if __name__ == "__main__":
    logger.add("Torrent_Test.log")
    
    print("Testing Torrent Metadata Module...")
    
    # Create Test File
    Test_Dir = Path("Test_Files")
    Test_Dir.mkdir(exist_ok=True)
    Test_File = Test_Dir / "Test.txt"
    Test_File.write_text("This Is A Test File For Torrent Creation!")
    
    print("\n1. Creating Test Torrent...")
    Metadata = Create_Torrent_From_Path(
        Test_File,
        "Test.dst",
        ["http://tracker.example.com:5043/announce"],
        Comment="Test Torrent"
    )
    print(f"✓ Created Torrent: {Metadata.Name}")
    print(f"  Info Hash: {Metadata.Info_Hash}")
    print(f"  Pieces: {Metadata.Get_Piece_Count()}")
    
    print("\n2. Loading Torrent...")
    Handler = DST_File_Handler()
    Loaded = Handler.Load_Torrent(Path("Test.dst"))
    print(f"✓ Loaded Torrent: {Loaded.Name}")
    
    print("\n✓ All Torrent Tests Passed!")
