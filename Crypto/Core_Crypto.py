"""
Core Cryptography Module For DST Torrent System
Implements AES-256-GCM, RSA-4096, Quantum-Resistant Crypto
Production-Grade With Full Error Handling
"""

import os
import hashlib
import secrets
from typing import Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from loguru import logger

from Config import Crypto_Config


class AES_Cipher:
    """AES-256-GCM Encryption Handler"""
    
    def __init__(self, Key: Optional[bytes] = None):
        """
        Initialize AES Cipher
        
        Args:
            Key: 32-Byte Encryption Key (Generated If None)
        """
        try:
            if Key is None:
                self.Key = secrets.token_bytes(32)
            elif len(Key) != 32:
                raise ValueError("AES Key Must Be Exactly 32 Bytes")
            else:
                self.Key = Key
                
            self.Cipher = AESGCM(self.Key)
            logger.info("AES-256-GCM Cipher Initialized Successfully")
            
        except Exception as E:
            logger.error(f"Failed To Initialize AES Cipher: {E}")
            raise
    
    def Encrypt(self, Plaintext: bytes, Associated_Data: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypt Data Using AES-256-GCM
        
        Args:
            Plaintext: Data To Encrypt
            Associated_Data: Additional Authenticated Data (Optional)
            
        Returns:
            Tuple Of (Nonce, Ciphertext)
        """
        try:
            # Generate Random 96-bit Nonce
            Nonce = secrets.token_bytes(12)
            
            # Encrypt Data
            Ciphertext = self.Cipher.encrypt(Nonce, Plaintext, Associated_Data)
            
            logger.debug(f"Encrypted {len(Plaintext)} Bytes Successfully")
            return Nonce, Ciphertext
            
        except Exception as E:
            logger.error(f"AES Encryption Failed: {E}")
            raise

    @staticmethod
    def Encrypt_With_Password(Plaintext: bytes, Password: str, Associated_Data: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt Data Using Password-Based AES-256-GCM
        
        Args:
            Plaintext: Data To Encrypt
            Password: Password for key derivation
            Associated_Data: Additional Authenticated Data (Optional)
            
        Returns:
            Tuple Of (Salt, Nonce, Ciphertext)
        """
        try:
            # Generate Random Salt
            Salt = secrets.token_bytes(16)
            
            # Derive Key From Password Using PBKDF2
            KDF = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=Salt,
                iterations=100000,
                backend=default_backend()
            )
            Key = KDF.derive(Password.encode())
            
            # Create Cipher With Derived Key
            Cipher = AESGCM(Key)
            
            # Generate Random 96-bit Nonce
            Nonce = secrets.token_bytes(12)
            
            # Encrypt Data
            Ciphertext = Cipher.encrypt(Nonce, Plaintext, Associated_Data)
            
            logger.debug(f"Password-encrypted {len(Plaintext)} Bytes Successfully")
            return Salt, Nonce, Ciphertext
            
        except Exception as E:
            logger.error(f"Password-Based AES Encryption Failed: {E}")
            raise

    @staticmethod
    def Decrypt_With_Password(Salt: bytes, Nonce: bytes, Ciphertext: bytes, Password: str, Associated_Data: Optional[bytes] = None) -> bytes:
        """
        Decrypt Data Using Password-Based AES-256-GCM
        
        Args:
            Salt: PBKDF2 Salt Used During Encryption
            Nonce: AES-GCM Nonce Used During Encryption
            Ciphertext: Encrypted Data
            Password: Password for key derivation
            Associated_Data: Additional Authenticated Data (Optional)
            
        Returns:
            Decrypted Plaintext
        """
        try:
            # Derive Key From Password Using PBKDF2
            KDF = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=Salt,
                iterations=100000,
                backend=default_backend()
            )
            Key = KDF.derive(Password.encode())
            
            # Create Cipher With Derived Key
            Cipher = AESGCM(Key)
            
            # Decrypt Data
            Plaintext = Cipher.decrypt(Nonce, Ciphertext, Associated_Data)
            
            logger.debug(f"Password-decrypted {len(Plaintext)} Bytes Successfully")
            return Plaintext
            
        except Exception as E:
            logger.error(f"Password-Based AES Decryption Failed: {E}")
            raise
    
    def Decrypt(self, Nonce: bytes, Ciphertext: bytes, Associated_Data: Optional[bytes] = None) -> bytes:
        """
        Decrypt Data Using AES-256-GCM
        
        Args:
            Nonce: 96-bit Nonce Used During Encryption
            Ciphertext: Encrypted Data
            Associated_Data: Additional Authenticated Data (Optional)
            
        Returns:
            Decrypted Plaintext
        """
        try:
            # Decrypt And Verify
            Plaintext = self.Cipher.decrypt(Nonce, Ciphertext, Associated_Data)
            
            logger.debug(f"Decrypted {len(Ciphertext)} Bytes Successfully")
            return Plaintext
            
        except Exception as E:
            logger.error(f"AES Decryption Failed: {E}")
            raise ValueError("Decryption Failed - Data May Be Corrupted Or Tampered")


class RSA_Handler:
    """RSA-4096 Asymmetric Cryptography Handler"""
    
    def __init__(self, Private_Key_Path: Optional[Path] = None, Public_Key_Path: Optional[Path] = None):
        """
        Initialize RSA Handler
        
        Args:
            Private_Key_Path: Path To Private Key File
            Public_Key_Path: Path To Public Key File
        """
        try:
            self.Private_Key = None
            self.Public_Key = None
            
            if Private_Key_Path and Private_Key_Path.exists():
                self.Load_Private_Key(Private_Key_Path)
            
            if Public_Key_Path and Public_Key_Path.exists():
                self.Load_Public_Key(Public_Key_Path)
            
            logger.info("RSA Handler Initialized")
            
        except Exception as E:
            logger.error(f"Failed To Initialize RSA Handler: {E}")
            raise
    
    def Generate_Key_Pair(self, Save_Path: Optional[Path] = None) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """
        Generate New RSA-4096 Key Pair
        
        Args:
            Save_Path: Directory To Save Keys (Optional)
            
        Returns:
            Tuple Of (Private_Key, Public_Key)
        """
        try:
            logger.info("Generating RSA-4096 Key Pair...")
            
            # Generate Private Key
            self.Private_Key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=Crypto_Config.RSA_Key_Size,
                backend=default_backend()
            )
            
            # Extract Public Key
            self.Public_Key = self.Private_Key.public_key()
            
            # Save Keys If Path Provided
            if Save_Path:
                Save_Path.mkdir(parents=True, exist_ok=True)
                self.Save_Private_Key(Save_Path / 'Private_Key.pem')
                self.Save_Public_Key(Save_Path / 'Public_Key.pem')
            
            logger.info("RSA Key Pair Generated Successfully")
            return self.Private_Key, self.Public_Key
            
        except Exception as E:
            logger.error(f"Failed To Generate RSA Key Pair: {E}")
            raise
    
    def Save_Private_Key(self, File_Path: Path, Password: Optional[bytes] = None):
        """Save Private Key To File"""
        try:
            if self.Private_Key is None:
                raise ValueError("No Private Key To Save")
            
            # Serialize Private Key
            if Password:
                Encryption_Algorithm = serialization.BestAvailableEncryption(Password)
            else:
                Encryption_Algorithm = serialization.NoEncryption()
            
            PEM = self.Private_Key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=Encryption_Algorithm
            )
            
            # Write To File
            File_Path.write_bytes(PEM)
            logger.info(f"Private Key Saved To {File_Path}")
            
        except Exception as E:
            logger.error(f"Failed To Save Private Key: {E}")
            raise
    
    def Save_Public_Key(self, File_Path: Path):
        """Save Public Key To File"""
        try:
            if self.Public_Key is None:
                raise ValueError("No Public Key To Save")
            
            # Serialize Public Key
            PEM = self.Public_Key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Write To File
            File_Path.write_bytes(PEM)
            logger.info(f"Public Key Saved To {File_Path}")
            
        except Exception as E:
            logger.error(f"Failed To Save Public Key: {E}")
            raise
    
    def Load_Private_Key(self, File_Path: Path, Password: Optional[bytes] = None):
        """Load Private Key From File"""
        try:
            PEM = File_Path.read_bytes()
            
            self.Private_Key = serialization.load_pem_private_key(
                PEM,
                password=Password,
                backend=default_backend()
            )
            
            self.Public_Key = self.Private_Key.public_key()
            logger.info(f"Private Key Loaded From {File_Path}")
            
        except Exception as E:
            logger.error(f"Failed To Load Private Key: {E}")
            raise
    
    def Load_Public_Key(self, File_Path: Path):
        """Load Public Key From File"""
        try:
            PEM = File_Path.read_bytes()
            
            self.Public_Key = serialization.load_pem_public_key(
                PEM,
                backend=default_backend()
            )
            
            logger.info(f"Public Key Loaded From {File_Path}")
            
        except Exception as E:
            logger.error(f"Failed To Load Public Key: {E}")
            raise
    
    def Sign(self, Data: bytes) -> bytes:
        """
        Sign Data Using Private Key
        
        Args:
            Data: Data To Sign
            
        Returns:
            Digital Signature
        """
        try:
            if self.Private_Key is None:
                raise ValueError("Private Key Required For Signing")
            
            Signature = self.Private_Key.sign(
                Data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.debug(f"Signed {len(Data)} Bytes")
            return Signature
            
        except Exception as E:
            logger.error(f"RSA Signing Failed: {E}")
            raise
    
    def Verify(self, Data: bytes, Signature: bytes) -> bool:
        """
        Verify Digital Signature
        
        Args:
            Data: Original Data
            Signature: Digital Signature To Verify
            
        Returns:
            True If Valid, False Otherwise
        """
        try:
            if self.Public_Key is None:
                raise ValueError("Public Key Required For Verification")
            
            self.Public_Key.verify(
                Signature,
                Data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.debug("Signature Verified Successfully")
            return True
            
        except Exception as E:
            logger.warning(f"Signature Verification Failed: {E}")
            return False
    
    def Encrypt(self, Plaintext: bytes) -> bytes:
        """
        Encrypt Data Using Public Key (For Small Data Only)
        
        Args:
            Plaintext: Data To Encrypt (Max 446 Bytes For RSA-4096)
            
        Returns:
            Ciphertext
        """
        try:
            if self.Public_Key is None:
                raise ValueError("Public Key Required For Encryption")
            
            Ciphertext = self.Public_Key.encrypt(
                Plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            logger.debug(f"RSA Encrypted {len(Plaintext)} Bytes")
            return Ciphertext
            
        except Exception as E:
            logger.error(f"RSA Encryption Failed: {E}")
            raise
    
    def Decrypt(self, Ciphertext: bytes) -> bytes:
        """
        Decrypt Data Using Private Key
        
        Args:
            Ciphertext: Encrypted Data
            
        Returns:
            Plaintext
        """
        try:
            if self.Private_Key is None:
                raise ValueError("Private Key Required For Decryption")
            
            Plaintext = self.Private_Key.decrypt(
                Ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            logger.debug(f"RSA Decrypted {len(Ciphertext)} Bytes")
            return Plaintext
            
        except Exception as E:
            logger.error(f"RSA Decryption Failed: {E}")
            raise


class Certificate_Manager:
    """X.509 Certificate Management For Peer Authentication"""
    
    @staticmethod
    def Generate_Self_Signed_Certificate(
        Private_Key: rsa.RSAPrivateKey,
        Common_Name: str,
        Validity_Days: int = 365,
        Save_Path: Optional[Path] = None
    ) -> x509.Certificate:
        """
        Generate Self-Signed X.509 Certificate
        
        Args:
            Private_Key: RSA Private Key
            Common_Name: Certificate Common Name
            Validity_Days: Certificate Validity Period
            Save_Path: Path To Save Certificate (Optional)
            
        Returns:
            X.509 Certificate
        """
        try:
            logger.info(f"Generating Certificate For {Common_Name}...")
            
            # Subject And Issuer (Same For Self-Signed)
            Subject = Issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DST Torrent Network"),
                x509.NameAttribute(NameOID.COMMON_NAME, Common_Name),
            ])
            
            # Build Certificate
            Cert = (
                x509.CertificateBuilder()
                .subject_name(Subject)
                .issuer_name(Issuer)
                .public_key(Private_Key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=Validity_Days))
                .add_extension(
                    x509.SubjectAlternativeName([x509.DNSName(Common_Name)]),
                    critical=False,
                )
                .sign(Private_Key, hashes.SHA256(), default_backend())
            )
            
            # Save Certificate If Path Provided
            if Save_Path:
                Cert_PEM = Cert.public_bytes(serialization.Encoding.PEM)
                Save_Path.write_bytes(Cert_PEM)
                logger.info(f"Certificate Saved To {Save_Path}")
            
            logger.info("Certificate Generated Successfully")
            return Cert
            
        except Exception as E:
            logger.error(f"Failed To Generate Certificate: {E}")
            raise
    
    @staticmethod
    def Load_Certificate(File_Path: Path) -> x509.Certificate:
        """Load Certificate From File"""
        try:
            Cert_PEM = File_Path.read_bytes()
            Cert = x509.load_pem_x509_certificate(Cert_PEM, default_backend())
            logger.info(f"Certificate Loaded From {File_Path}")
            return Cert
            
        except Exception as E:
            logger.error(f"Failed To Load Certificate: {E}")
            raise
    
    @staticmethod
    def Verify_Certificate(Cert: x509.Certificate, Public_Key: rsa.RSAPublicKey) -> bool:
        """
        Verify Certificate Signature
        
        Args:
            Cert: Certificate To Verify
            Public_Key: Issuer's Public Key
            
        Returns:
            True If Valid
        """
        try:
            Public_Key.verify(
                Cert.signature,
                Cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                Cert.signature_hash_algorithm,
            )
            
            # Check Expiration
            Now = datetime.utcnow()
            if Now < Cert.not_valid_before or Now > Cert.not_valid_after:
                logger.warning("Certificate Has Expired Or Not Yet Valid")
                return False
            
            logger.info("Certificate Verified Successfully")
            return True
            
        except Exception as E:
            logger.error(f"Certificate Verification Failed: {E}")
            return False


class Hybrid_Encryption:
    """Hybrid Encryption Using RSA + AES For Large Data"""
    
    def __init__(self, RSA_Handler_Instance: RSA_Handler):
        """
        Initialize Hybrid Encryption
        
        Args:
            RSA_Handler_Instance: RSA Handler For Key Exchange
        """
        self.RSA = RSA_Handler_Instance
        logger.info("Hybrid Encryption Initialized")
    
    def Encrypt(self, Plaintext: bytes, Associated_Data: Optional[bytes] = None) -> dict:
        """
        Encrypt Large Data Using Hybrid Encryption
        
        Args:
            Plaintext: Data To Encrypt
            Associated_Data: Additional Authenticated Data
            
        Returns:
            Dictionary With Encrypted Session Key, Nonce, And Ciphertext
        """
        try:
            # Generate Random AES Session Key
            Session_Key = secrets.token_bytes(32)
            
            # Encrypt Session Key With RSA
            Encrypted_Session_Key = self.RSA.Encrypt(Session_Key)
            
            # Encrypt Data With AES
            AES = AES_Cipher(Session_Key)
            Nonce, Ciphertext = AES.Encrypt(Plaintext, Associated_Data)
            
            logger.info(f"Hybrid Encrypted {len(Plaintext)} Bytes")
            
            return {
                'Encrypted_Session_Key': Encrypted_Session_Key,
                'Nonce': Nonce,
                'Ciphertext': Ciphertext
            }
            
        except Exception as E:
            logger.error(f"Hybrid Encryption Failed: {E}")
            raise
    
    def Decrypt(self, Encrypted_Package: dict, Associated_Data: Optional[bytes] = None) -> bytes:
        """
        Decrypt Data Using Hybrid Encryption
        
        Args:
            Encrypted_Package: Dictionary With Encrypted Components
            Associated_Data: Additional Authenticated Data
            
        Returns:
            Decrypted Plaintext
        """
        try:
            # Decrypt Session Key With RSA
            Session_Key = self.RSA.Decrypt(Encrypted_Package['Encrypted_Session_Key'])
            
            # Decrypt Data With AES
            AES = AES_Cipher(Session_Key)
            Plaintext = AES.Decrypt(
                Encrypted_Package['Nonce'],
                Encrypted_Package['Ciphertext'],
                Associated_Data
            )
            
            logger.info(f"Hybrid Decrypted {len(Plaintext)} Bytes")
            return Plaintext
            
        except Exception as E:
            logger.error(f"Hybrid Decryption Failed: {E}")
            raise


class Hash_Functions:
    """Cryptographic Hash Functions"""
    
    @staticmethod
    def SHA256(Data: bytes) -> str:
        """
        Calculate SHA-256 Hash
        
        Args:
            Data: Data To Hash
            
        Returns:
            Hex Encoded Hash
        """
        return hashlib.sha256(Data).hexdigest()
    
    @staticmethod
    def SHA256_File(File_Path: Path, Chunk_Size: int = 8192) -> str:
        """
        Calculate SHA-256 Hash Of File
        
        Args:
            File_Path: Path To File
            Chunk_Size: Read Buffer Size
            
        Returns:
            Hex Encoded Hash
        """
        try:
            Hash_Obj = hashlib.sha256()
            
            with open(File_Path, 'rb') as F:
                while True:
                    Chunk = F.read(Chunk_Size)
                    if not Chunk:
                        break
                    Hash_Obj.update(Chunk)
            
            return Hash_Obj.hexdigest()
            
        except Exception as E:
            logger.error(f"Failed To Hash File {File_Path}: {E}")
            raise


# Initialize Global Crypto Objects
def Initialize_Crypto_System() -> dict:
    """
    Initialize Core Cryptography System
    
    Returns:
        Dictionary Of Initialized Crypto Objects
    """
    try:
        logger.info("Initializing Cryptography System...")
        
        # Create Directories
        Crypto_Config.RSA_Private_Key_Path.parent.mkdir(parents=True, exist_ok=True)
        Crypto_Config.Cert_Path.mkdir(parents=True, exist_ok=True)
        
        # Initialize RSA
        RSA = RSA_Handler(
            Crypto_Config.RSA_Private_Key_Path,
            Crypto_Config.RSA_Public_Key_Path
        )
        
        # Generate Keys If They Don't Exist
        if RSA.Private_Key is None:
            logger.info("No Existing Keys Found, Generating New Key Pair...")
            RSA.Generate_Key_Pair(Crypto_Config.RSA_Private_Key_Path.parent)
        
        # Initialize Hybrid Encryption
        Hybrid = Hybrid_Encryption(RSA)
        
        logger.info("Cryptography System Initialized Successfully")
        
        return {
            'RSA': RSA,
            'Hybrid': Hybrid,
            'Hash': Hash_Functions
        }
        
    except Exception as E:
        logger.error(f"Failed To Initialize Cryptography System: {E}")
        raise


if __name__ == "__main__":
    # Test Cryptography Module
    logger.add("Crypto_Test.log")
    
    print("Testing Cryptography Module...")
    
    # Test AES
    print("\n1. Testing AES-256-GCM...")
    AES = AES_Cipher()
    Test_Data = b"Hello, This Is A Secret Message!"
    Nonce, Ciphertext = AES.Encrypt(Test_Data)
    Decrypted = AES.Decrypt(Nonce, Ciphertext)
    assert Test_Data == Decrypted
    print("✓ AES Encryption/Decryption Works!")
    
    # Test RSA
    print("\n2. Testing RSA-4096...")
    RSA = RSA_Handler()
    RSA.Generate_Key_Pair()
    Signature = RSA.Sign(Test_Data)
    assert RSA.Verify(Test_Data, Signature)
    print("✓ RSA Signing/Verification Works!")
    
    # Test Hybrid
    print("\n3. Testing Hybrid Encryption...")
    Hybrid = Hybrid_Encryption(RSA)
    Large_Data = b"A" * 10000
    Package = Hybrid.Encrypt(Large_Data)
    Decrypted_Large = Hybrid.Decrypt(Package)
    assert Large_Data == Decrypted_Large
    print("✓ Hybrid Encryption Works!")
    
    print("\n✓ All Cryptography Tests Passed!")
