"""
Quantum-Resistant Cryptography Module
Implements Post-Quantum Algorithms (CRYSTALS-Kyber, Dilithium)
"""

import os
import secrets
from typing import Tuple, Optional
from loguru import logger

try:
    import oqs
    QUANTUM_AVAILABLE = True
except ImportError:
    QUANTUM_AVAILABLE = False
    logger.warning("liboqs Not Available - Quantum-Resistant Crypto Disabled")


class Quantum_Key_Exchange:
    """Quantum-Resistant Key Exchange Using CRYSTALS-Kyber"""
    
    def __init__(self, Algorithm: str = "Kyber1024"):
        """
        Initialize Quantum Key Exchange
        
        Args:
            Algorithm: Kyber Variant (Kyber512, Kyber768, Kyber1024)
        """
        if not QUANTUM_AVAILABLE:
            raise ImportError("liboqs Library Not Available")
        
        try:
            self.Algorithm = Algorithm
            self.KEM = oqs.KeyEncapsulation(Algorithm)
            logger.info(f"Quantum Key Exchange Initialized With {Algorithm}")
            
        except Exception as E:
            logger.error(f"Failed To Initialize Quantum Key Exchange: {E}")
            raise
    
    def Generate_Keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate Quantum-Resistant Key Pair
        
        Returns:
            Tuple Of (Public_Key, Secret_Key)
        """
        try:
            Public_Key = self.KEM.generate_keypair()
            Secret_Key = self.KEM.export_secret_key()
            
            logger.info("Quantum Keypair Generated")
            return Public_Key, Secret_Key
            
        except Exception as E:
            logger.error(f"Failed To Generate Quantum Keypair: {E}")
            raise
    
    def Encapsulate(self, Public_Key: bytes) -> Tuple[bytes, bytes]:
        """
        Encapsulate Shared Secret
        
        Args:
            Public_Key: Recipient's Public Key
            
        Returns:
            Tuple Of (Ciphertext, Shared_Secret)
        """
        try:
            Ciphertext, Shared_Secret = self.KEM.encap_secret(Public_Key)
            
            logger.debug("Shared Secret Encapsulated")
            return Ciphertext, Shared_Secret
            
        except Exception as E:
            logger.error(f"Failed To Encapsulate: {E}")
            raise
    
    def Decapsulate(self, Ciphertext: bytes) -> bytes:
        """
        Decapsulate Shared Secret
        
        Args:
            Ciphertext: Encapsulated Secret
            
        Returns:
            Shared Secret
        """
        try:
            Shared_Secret = self.KEM.decap_secret(Ciphertext)
            
            logger.debug("Shared Secret Decapsulated")
            return Shared_Secret
            
        except Exception as E:
            logger.error(f"Failed To Decapsulate: {E}")
            raise


class Quantum_Signature:
    """Quantum-Resistant Digital Signatures Using CRYSTALS-Dilithium"""
    
    def __init__(self, Algorithm: str = "Dilithium5"):
        """
        Initialize Quantum Signature
        
        Args:
            Algorithm: Dilithium Variant (Dilithium2, Dilithium3, Dilithium5)
        """
        if not QUANTUM_AVAILABLE:
            raise ImportError("liboqs Library Not Available")
        
        try:
            self.Algorithm = Algorithm
            self.Sig = oqs.Signature(Algorithm)
            logger.info(f"Quantum Signature Initialized With {Algorithm}")
            
        except Exception as E:
            logger.error(f"Failed To Initialize Quantum Signature: {E}")
            raise
    
    def Generate_Keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate Quantum-Resistant Signature Key Pair
        
        Returns:
            Tuple Of (Public_Key, Secret_Key)
        """
        try:
            Public_Key = self.Sig.generate_keypair()
            Secret_Key = self.Sig.export_secret_key()
            
            logger.info("Quantum Signature Keypair Generated")
            return Public_Key, Secret_Key
            
        except Exception as E:
            logger.error(f"Failed To Generate Signature Keypair: {E}")
            raise
    
    def Sign(self, Message: bytes) -> bytes:
        """
        Sign Message With Quantum-Resistant Algorithm
        
        Args:
            Message: Data To Sign
            
        Returns:
            Signature
        """
        try:
            Signature = self.Sig.sign(Message)
            
            logger.debug(f"Signed {len(Message)} Bytes")
            return Signature
            
        except Exception as E:
            logger.error(f"Failed To Sign Message: {E}")
            raise
    
    def Verify(self, Message: bytes, Signature: bytes, Public_Key: bytes) -> bool:
        """
        Verify Quantum-Resistant Signature
        
        Args:
            Message: Original Message
            Signature: Signature To Verify
            Public_Key: Signer's Public Key
            
        Returns:
            True If Valid
        """
        try:
            Is_Valid = self.Sig.verify(Message, Signature, Public_Key)
            
            if Is_Valid:
                logger.debug("Quantum Signature Verified")
            else:
                logger.warning("Quantum Signature Verification Failed")
            
            return Is_Valid
            
        except Exception as E:
            logger.error(f"Signature Verification Error: {E}")
            return False


def Initialize_Quantum_Crypto() -> Optional[dict]:
    """
    Initialize Quantum-Resistant Cryptography
    
    Returns:
        Dictionary Of Quantum Crypto Objects Or None
    """
    if not QUANTUM_AVAILABLE:
        logger.warning("Quantum Cryptography Not Available")
        return None
    
    try:
        logger.info("Initializing Quantum-Resistant Cryptography...")
        
        Quantum_KEM = Quantum_Key_Exchange("Kyber1024")
        Quantum_Sig = Quantum_Signature("Dilithium5")
        
        logger.info("Quantum Cryptography Initialized Successfully")
        
        return {
            'KEM': Quantum_KEM,
            'Signature': Quantum_Sig
        }
        
    except Exception as E:
        logger.error(f"Failed To Initialize Quantum Cryptography: {E}")
        return None


if __name__ == "__main__":
    logger.add("Quantum_Test.log")
    
    if QUANTUM_AVAILABLE:
        print("Testing Quantum-Resistant Cryptography...")
        
        # Test Key Exchange
        print("\n1. Testing Kyber Key Exchange...")
        KEM = Quantum_Key_Exchange()
        Pub, Sec = KEM.Generate_Keypair()
        Ct, Ss1 = KEM.Encapsulate(Pub)
        Ss2 = KEM.Decapsulate(Ct)
        assert Ss1 == Ss2
        print("✓ Quantum Key Exchange Works!")
        
        # Test Signatures
        print("\n2. Testing Dilithium Signatures...")
        Sig = Quantum_Signature()
        Pub, Sec = Sig.Generate_Keypair()
        Message = b"Test Message"
        Signature = Sig.Sign(Message)
        assert Sig.Verify(Message, Signature, Pub)
        print("✓ Quantum Signatures Work!")
        
        print("\n✓ All Quantum Tests Passed!")
    else:
        print("Quantum Cryptography Not Available - Install liboqs-python")
