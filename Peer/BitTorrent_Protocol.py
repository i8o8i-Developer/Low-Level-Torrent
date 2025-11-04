"""
BitTorrent Peer Wire Protocol Implementation
Full P2P File Sharing With Piece Verification
"""

import asyncio
import hashlib
import struct
import random
import time
from typing import Optional, List, Dict, Set, Tuple
from dataclasses import dataclass
from loguru import logger

from Peer import Peer_Connection
from Core import Torrent_Metadata


@dataclass
class Peer_State:
    """Tracks Peer Connection State"""
    peer_id: str
    ip: str
    port: int
    connected: bool = False
    choked: bool = True
    interested: bool = False
    peer_choked: bool = True
    peer_interested: bool = False
    bitfield: bytes = b''
    requested_pieces: Set[int] = None
    downloaded_pieces: Set[int] = None

    def __post_init__(self):
        self.requested_pieces = set()
        self.downloaded_pieces = set()


class BitTorrent_Protocol:
    """BitTorrent Peer Wire Protocol Handler"""

    # Protocol Constants
    PROTOCOL_STRING = b'BitTorrent protocol'
    HANDSHAKE_LENGTH = 80  # 1 + 19 + 8 + 32 (SHA-256) + 20 = 80
    BLOCK_SIZE = 16384  # 16KB Blocks

    # Message IDs
    MSG_CHOKE = 0
    MSG_UNCHOKE = 1
    MSG_INTERESTED = 2
    MSG_NOT_INTERESTED = 3
    MSG_HAVE = 4
    MSG_BITFIELD = 5
    MSG_REQUEST = 6
    MSG_PIECE = 7
    MSG_CANCEL = 8
    MSG_PORT = 9

    def __init__(self, torrent_metadata: Torrent_Metadata, peer_id: str):
        """
        Initialize BitTorrent Protocol

        Args:
            torrent_metadata: Torrent MetaData
            peer_id: Our Peer ID
        """
        self.metadata = torrent_metadata
        self.peer_id = peer_id
        self.info_hash = bytes.fromhex(torrent_metadata.Info_Hash)

        # Piece Management
        self.total_pieces = len(torrent_metadata.Piece_Hashes)
        self.piece_size = torrent_metadata.Piece_Size
        self.have_pieces = set()  # Pieces We Have
        self.requested_pieces = set()  # Pieces We Have Requested

        # Piece Buffer: piece_index -> {block_offset: block_data}
        self.piece_buffers: Dict[int, Dict[int, bytes]] = {}

        # Download Directory
        self.download_dir = None

        # Peer Management
        self.peers: Dict[str, Peer_State] = {}
        self.active_peers: Dict[str, Peer_Connection] = {}

        # Download State
        self.downloaded_bytes = 0
        self.uploaded_bytes = 0
        self.files_written = set()  # Track Which Files We've Written

        logger.info(f"BitTorrent Protocol Initialized for {torrent_metadata.Name}")

    def create_handshake(self) -> bytes:
        """Create BitTorrent Handshake Message"""
        pstrlen = bytes([len(self.PROTOCOL_STRING)])
        pstr = self.PROTOCOL_STRING
        reserved = b'\x00' * 8
        info_hash = self.info_hash
        peer_id = self.peer_id.encode()

        return pstrlen + pstr + reserved + info_hash + peer_id

    def parse_handshake(self, data: bytes) -> Optional[Tuple[bytes, bytes]]:
        """Parse Incoming Handshake"""
        if len(data) != self.HANDSHAKE_LENGTH:
            return None

        pstrlen = data[0]
        if pstrlen != len(self.PROTOCOL_STRING):
            return None

        pstr = data[1:1+pstrlen]
        if pstr != self.PROTOCOL_STRING:
            return None

        # SHA-256 info hash is 32 bytes
        info_hash = data[1+pstrlen+8:1+pstrlen+8+32]
        peer_id = data[1+pstrlen+8+32:1+pstrlen+8+32+20]

        return info_hash, peer_id

    def create_message(self, msg_id: int, payload: bytes = b'') -> bytes:
        """Create A BitTorrent Message"""
        length = 1 + len(payload)
        return struct.pack('>I', length) + bytes([msg_id]) + payload

    def parse_message(self, data: bytes) -> Optional[Tuple[int, bytes]]:
        """Parse A BitTorrent Message"""
        if len(data) < 4:
            return None

        length = struct.unpack('>I', data[:4])[0]
        if length == 0:  # Keep-Alive
            return None

        if len(data) < 4 + length:
            return None

        msg_id = data[4]
        payload = data[5:4+length]

        return msg_id, payload

    def create_have_message(self, piece_index: int) -> bytes:
        """Create HAVE Message"""
        payload = struct.pack('>I', piece_index)
        return self.create_message(self.MSG_HAVE, payload)

    def create_bitfield_message(self) -> bytes:
        """Create BITFIELD Message"""
        # Create BitField From Have_Pieces
        bitfield = bytearray((self.total_pieces + 7) // 8)
        for piece in self.have_pieces:
            byte_index = piece // 8
            bit_index = piece % 8
            bitfield[byte_index] |= (1 << (7 - bit_index))

        return self.create_message(self.MSG_BITFIELD, bytes(bitfield))

    def create_request_message(self, piece_index: int, block_offset: int, block_length: int) -> bytes:
        """Create REQUEST Message"""
        payload = struct.pack('>III', piece_index, block_offset, block_length)
        return self.create_message(self.MSG_REQUEST, payload)

    def parse_have_message(self, payload: bytes) -> Optional[int]:
        """Parse HAVE Message"""
        if len(payload) != 4:
            return None
        return struct.unpack('>I', payload)[0]

    def parse_bitfield_message(self, payload: bytes) -> Set[int]:
        """Parse BITFIELD Message"""
        pieces = set()
        for byte_index, byte_value in enumerate(payload):
            for bit_index in range(8):
                if byte_value & (1 << (7 - bit_index)):
                    piece_index = byte_index * 8 + bit_index
                    if piece_index < self.total_pieces:
                        pieces.add(piece_index)
        return pieces

    def parse_request_message(self, payload: bytes) -> Optional[Tuple[int, int, int]]:
        """Parse REQUEST Message"""
        if len(payload) != 12:
            return None
        return struct.unpack('>III', payload)

    def parse_piece_message(self, payload: bytes) -> Optional[Tuple[int, int, bytes]]:
        """Parse PIECE Message"""
        if len(payload) < 8:
            return None
        piece_index, block_offset = struct.unpack('>II', payload[:8])
        block_data = payload[8:]
        return piece_index, block_offset, block_data

    async def perform_handshake(self, peer_conn: Peer_Connection) -> bool:
        """Perform BitTorrent Handshake With Peer"""
        try:
            # Send HandShake (No Length Prefix)
            handshake = self.create_handshake()
            success = await peer_conn.Send_Handshake(handshake)
            if not success:
                return False

            # Receive HandShake (No Length Prefix)
            response = await peer_conn.Receive_Handshake()
            if not response or len(response) != self.HANDSHAKE_LENGTH:
                return False

            parsed = self.parse_handshake(response)
            if not parsed:
                return False

            peer_info_hash, peer_peer_id = parsed

            # Verify Info Hash Matches
            if peer_info_hash != self.info_hash:
                logger.warning(f"Info Hash Mismatch From Peer {peer_conn.Peer_Id}")
                logger.debug(f"Expected: {self.info_hash.hex()}")
                logger.debug(f"Received: {peer_info_hash.hex()}")
                return False

            peer_id_str = peer_peer_id.decode('latin-1')
            logger.info(f"Handshake Successful With Peer {peer_id_str}")

            # Initialize Peer State
            self.peers[peer_conn.Peer_Id] = Peer_State(
                peer_id=peer_id_str,
                ip=peer_conn.IP,
                port=peer_conn.Port,
                connected=True
            )

            return True

        except Exception as e:
            logger.error(f"Handshake Failed With {peer_conn.Peer_Id}: {e}")
            return False

    async def handle_peer_messages(self, peer_conn: Peer_Connection):
        """Handle Incoming Messages From A Peer"""
        peer_state = self.peers.get(peer_conn.Peer_Id)
        if not peer_state:
            return

        try:
            while peer_state.connected:
                data = await peer_conn.Receive_Message()
                if not data:
                    break

                msg = self.parse_message(data)
                if not msg:
                    continue

                msg_id, payload = msg
                await self.process_message(peer_conn, msg_id, payload)

        except Exception as e:
            logger.error(f"Error Handling Messages From {peer_conn.Peer_Id}: {e}")
        finally:
            peer_state.connected = False

    async def process_message(self, peer_conn: Peer_Connection, msg_id: int, payload: bytes):
        """Process Incoming Peer Message"""
        peer_state = self.peers.get(peer_conn.Peer_Id)
        if not peer_state:
            return

        if msg_id == self.MSG_CHOKE:
            peer_state.peer_choked = True
            logger.debug(f"Peer {peer_conn.Peer_Id} Choked Us")

        elif msg_id == self.MSG_UNCHOKE:
            peer_state.peer_choked = False
            logger.debug(f"Peer {peer_conn.Peer_Id} Unchoked Us")
            # Start Requesting Pieces If We're Interested
            if peer_state.interested:
                await self.request_pieces_from_peer(peer_conn)

        elif msg_id == self.MSG_INTERESTED:
            peer_state.peer_interested = True
            logger.debug(f"Peer {peer_conn.Peer_Id} Is Interested")

        elif msg_id == self.MSG_NOT_INTERESTED:
            peer_state.peer_interested = False
            logger.debug(f"Peer {peer_conn.Peer_Id} Is Not Interested")

        elif msg_id == self.MSG_HAVE:
            piece_index = self.parse_have_message(payload)
            if piece_index is not None:
                peer_state.downloaded_pieces.add(piece_index)
                logger.debug(f"Peer {peer_conn.Peer_Id} Has Piece {piece_index}")

        elif msg_id == self.MSG_BITFIELD:
            peer_state.downloaded_pieces = self.parse_bitfield_message(payload)
            logger.debug(f"Peer {peer_conn.Peer_Id} Has {len(peer_state.downloaded_pieces)} Pieces")

            # Send Interested If Peer Has Pieces We Want
            wanted_pieces = peer_state.downloaded_pieces - self.have_pieces
            if wanted_pieces:
                await self.send_interested(peer_conn)

        elif msg_id == self.MSG_REQUEST:
            # Handle Piece Requests (For Seeding)
            request_info = self.parse_request_message(payload)
            if request_info:
                piece_index, block_offset, block_length = request_info
                await self.send_piece_block(peer_conn, piece_index, block_offset, block_length)

        elif msg_id == self.MSG_PIECE:
            # Handle Received Piece Block
            piece_info = self.parse_piece_message(payload)
            if piece_info:
                piece_index, block_offset, block_data = piece_info
                await self.handle_received_block(peer_conn, piece_index, block_offset, block_data)

        elif msg_id == self.MSG_CANCEL:
            # Handle Cancel (Rarely Used)
            pass

    async def send_interested(self, peer_conn: Peer_Connection):
        """Send INTERESTED Message"""
        peer_state = self.peers.get(peer_conn.Peer_Id)
        if peer_state and not peer_state.interested:
            msg = self.create_message(self.MSG_INTERESTED)
            await peer_conn.Send_Message(msg)
            peer_state.interested = True
            logger.debug(f"Sent INTERESTED To {peer_conn.Peer_Id}")

    async def request_pieces_from_peer(self, peer_conn: Peer_Connection):
        """Request Pieces From A Peer With Rarest-First Strategy"""
        peer_state = self.peers.get(peer_conn.Peer_Id)
        if not peer_state or peer_state.peer_choked:
            return

        # Find Pieces This Peer Has That We Don't
        available_pieces = peer_state.downloaded_pieces - self.have_pieces - self.requested_pieces

        if not available_pieces:
            return

        # Implement Rarest-First Piece Selection
        # Count How Many Peers Have Each Piece (Rarity)
        piece_rarity = {}
        for piece in available_pieces:
            rarity = sum(1 for p in self.peers.values() 
                        if p.downloaded_pieces and piece in p.downloaded_pieces)
            piece_rarity[piece] = rarity

        # Sort By Rarity (Lowest First) Then By Piece Index
        sorted_pieces = sorted(piece_rarity.keys(), key=lambda p: (piece_rarity[p], p))

        # Request Up To 5 Pieces At A Time
        pieces_to_request = sorted_pieces[:5]

        for piece_index in pieces_to_request:
            if piece_index in self.requested_pieces:
                continue

            self.requested_pieces.add(piece_index)

            # Calculate Block Requests For This Piece
            piece_size = min(self.piece_size,
                           self.metadata.Get_Total_Size() - piece_index * self.piece_size)

            blocks_needed = (piece_size + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE

            for block_index in range(blocks_needed):
                block_offset = block_index * self.BLOCK_SIZE
                block_length = min(self.BLOCK_SIZE, piece_size - block_offset)

                request_msg = self.create_request_message(piece_index, block_offset, block_length)
                await peer_conn.Send_Message(request_msg)

                logger.debug(f"Requested Piece {piece_index}, Block {block_index} From {peer_conn.Peer_Id}")

    async def handle_received_block(self, peer_conn: Peer_Connection, piece_index: int,
                                  block_offset: int, block_data: bytes):
        """Handle Received Piece Block With Full Implementation"""
        logger.debug(f"Received block for piece {piece_index}, offset {block_offset}, "
                    f"size {len(block_data)} from {peer_conn.Peer_Id}")

        # 1. Store The Block In Piece Buffer
        if piece_index not in self.piece_buffers:
            self.piece_buffers[piece_index] = {}

        self.piece_buffers[piece_index][block_offset] = block_data
        self.downloaded_bytes += len(block_data)

        # 2. Check If Piece Is Complete
        if self._is_piece_complete(piece_index):
            # 3. Verify Piece Hash
            if await self._verify_piece_hash(piece_index):
                logger.info(f"Piece {piece_index} Verified Successfully!")

                # 4. Write To Disk If Valid
                await self._write_piece_to_files(piece_index)

                # Mark Piece As Completed
                self.have_pieces.add(piece_index)
                self.requested_pieces.discard(piece_index)

                # Clean Up Piece Buffer
                if piece_index in self.piece_buffers:
                    del self.piece_buffers[piece_index]

                # 5. Send HAVE Message To All Peers
                await self._broadcast_have_message(piece_index)

                logger.info(f"Piece {piece_index} Completed And Saved. "
                           f"Progress: {self.get_download_progress():.1f}%")
            else:
                logger.warning(f"Piece {piece_index} Hash Verification Failed!")
                # Re-request The Piece
                if piece_index in self.piece_buffers:
                    del self.piece_buffers[piece_index]
                self.requested_pieces.discard(piece_index)

    async def send_piece_block(self, peer_conn: Peer_Connection, piece_index: int,
                             block_offset: int, block_length: int):
        """Send A Piece Block To A Peer (For Seeding)"""
        try:
            # Check If We Have This Piece
            if piece_index not in self.have_pieces:
                logger.debug(f"Don't Have Piece {piece_index} To Send")
                return

            # Read The Block From Files
            block_data = await self._read_block_from_files(piece_index, block_offset, block_length)

            if block_data and len(block_data) == block_length:
                # Create PIECE Message
                payload = struct.pack('>II', piece_index, block_offset) + block_data
                piece_msg = self.create_message(self.MSG_PIECE, payload)

                await peer_conn.Send_Message(piece_msg)
                self.uploaded_bytes += block_length

                logger.debug(f"Sent Piece {piece_index}, Block Offset {block_offset}, "
                            f"Length {block_length} To {peer_conn.Peer_Id}")
            else:
                logger.warning(f"Failed To Read Block For Piece {piece_index}")

        except Exception as e:
            logger.error(f"Error sending piece block: {e}")

    async def _read_block_from_files(self, piece_index: int, block_offset: int, block_length: int) -> Optional[bytes]:
        """Read A Block From The Downloaded Files For Seeding"""
        try:
            # Calculate Piece Offset In Torrent
            piece_offset = piece_index * self.piece_size

            # Find Which File Contains This Block
            current_offset = 0

            for file_info in self.metadata.Files:
                file_path = self.download_dir / file_info.Path if self.download_dir else file_info.Path
                file_start = current_offset
                file_end = current_offset + file_info.Length

                # Check If The Requested Block Is In This File
                block_start = piece_offset + block_offset
                block_end = block_start + block_length

                if block_start < file_end and block_end > file_start:
                    # Calculate Overlap With File
                    file_read_start = max(block_start - file_start, 0)
                    file_read_end = min(block_end - file_start, file_info.Length)

                    if file_read_start < file_read_end:
                        # Read From File
                        with open(file_path, 'rb') as f:
                            f.seek(file_read_start)
                            data = f.read(file_read_end - file_read_start)

                        # If This Is The Start Of The Block, Return It
                        if block_start >= file_start:
                            return data
                        else:
                            # Pad With Zeros If Block Starts Before File
                            padding = b'\x00' * (file_start - block_start)
                            return padding + data

                current_offset += file_info.Length

            return None

        except Exception as e:
            logger.error(f"Error Reading Block From Files: {e}")
            return None

    def _is_piece_complete(self, piece_index: int) -> bool:
        """Check If A Piece Has All Its Blocks"""
        if piece_index not in self.piece_buffers:
            return False

        piece_buffer = self.piece_buffers[piece_index]

        # Calculate Expected Piece Size
        total_size = self.metadata.Get_Total_Size()
        piece_size = min(self.piece_size,
                        total_size - piece_index * self.piece_size)

        # Calculate Expected Number Of Blocks
        expected_blocks = (piece_size + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE

        # Check If We Have All Blocks With Correct Total Size
        total_data_size = sum(len(block) for block in piece_buffer.values())

        # Verify We Have All Sequential Blocks From 0
        expected_offsets = set(range(0, piece_size, self.BLOCK_SIZE))
        actual_offsets = set(piece_buffer.keys())

        return (expected_offsets == actual_offsets and
                total_data_size == piece_size and
                len(piece_buffer) == expected_blocks)

    async def _verify_piece_hash(self, piece_index: int) -> bool:
        """Verify Piece Hash Against Torrent Metadata"""
        if piece_index not in self.piece_buffers:
            return False

        # Assemble Piece Data From Blocks
        piece_buffer = self.piece_buffers[piece_index]
        piece_data = b''

        # Sort Blocks By Offset And Concatenate
        for offset in sorted(piece_buffer.keys()):
            piece_data += piece_buffer[offset]

        # Calculate SHA-1 Hash
        piece_hash = hashlib.sha1(piece_data).digest()

        # Compare With Expected Hash From Torrent
        expected_hash = bytes.fromhex(self.metadata.Piece_Hashes[piece_index])

        return piece_hash == expected_hash

    async def _write_piece_to_files(self, piece_index: int):
        """Write Completed Piece Data To Appropriate Files"""
        if piece_index not in self.piece_buffers:
            logger.warning(f"Piece {piece_index} Not In Buffers!")
            return

        # Assemble Piece Data
        piece_buffer = self.piece_buffers[piece_index]
        piece_data = b''

        for offset in sorted(piece_buffer.keys()):
            piece_data += piece_buffer[offset]

        logger.info(f"Writing Piece {piece_index}, {len(piece_data)} Bytes To Files")
        logger.info(f"Download Directory: {self.download_dir}")
        logger.info(f"Files In Metadata: {len(self.metadata.Files)}")

        # Calculate Piece Offset In Torrent
        piece_offset = piece_index * self.piece_size
        piece_size = len(piece_data)

        # Find Which Files This Piece Belongs To
        current_offset = 0

        for file_info in self.metadata.Files:
            logger.info(f"Processing File: {file_info.Path}, Length: {file_info.Length}")
            
            if self.download_dir:
                file_path = self.download_dir / file_info.Path
            else:
                from pathlib import Path
                file_path = Path(file_info.Path)
            
            logger.info(f"Full File Path: {file_path}")
            
            file_start = current_offset
            file_end = current_offset + file_info.Length

            # Check If This Piece Overlaps With The File
            piece_start = piece_offset
            piece_end = piece_offset + piece_size

            if piece_start < file_end and piece_end > file_start:
                # Calculate Overlap
                overlap_start = max(piece_start, file_start)
                overlap_end = min(piece_end, file_end)

                if overlap_start < overlap_end:
                    # Calculate Data Offset In Piece And File
                    piece_data_start = overlap_start - piece_start
                    piece_data_end = overlap_end - piece_start
                    file_write_start = overlap_start - file_start

                    # Ensure Directory Exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write Data To File
                    with open(file_path, 'r+b' if file_path.exists() else 'wb') as f:
                        f.seek(file_write_start)
                        f.write(piece_data[piece_data_start:piece_data_end])

                    logger.info(f"✅ Wrote {piece_data_end - piece_data_start} Bytes To {file_path}")

            current_offset += file_info.Length

    async def _broadcast_have_message(self, piece_index: int):
        """Send HAVE Message To All Connected Peers"""
        have_msg = self.create_have_message(piece_index)

        for peer_conn in self.active_peers.values():
            try:
                await peer_conn.Send_Message(have_msg)
                logger.debug(f"Sent HAVE {piece_index} To {peer_conn.Peer_Id}")
            except Exception as e:
                logger.debug(f"Failed To Send HAVE To {peer_conn.Peer_Id}: {e}")

    def set_download_directory(self, download_dir: str):
        """Set The Download Directory"""
        from pathlib import Path
        self.download_dir = Path(download_dir)

    async def load_existing_pieces(self):
        """Load Existing Pieces From Downloaded Files For Seeding"""
        if not self.download_dir:
            logger.warning("No Download Directory Set For Loading Existing Pieces")
            return

        logger.info("Loading Existing Pieces From Downloaded Files...")

        try:
            # Check Each Piece By Reading And Verifying From Files
            for piece_index in range(self.total_pieces):
                if await self._verify_piece_from_files(piece_index):
                    self.have_pieces.add(piece_index)
                    logger.debug(f"Piece {piece_index} Verified And Loaded From Files")
                else:
                    logger.debug(f"Piece {piece_index} Not Available Or Corrupted")

            logger.info(f"Loaded {len(self.have_pieces)}/{self.total_pieces} Pieces From Existing Files")

        except Exception as e:
            logger.error(f"Error Loading Existing Pieces: {e}")

    async def _verify_piece_from_files(self, piece_index: int) -> bool:
        """Verify A Piece By Reading It From The Downloaded Files"""
        try:
            # Calculate Piece Offset In Torrent
            piece_offset = piece_index * self.piece_size
            piece_size = min(self.piece_size,
                           self.metadata.Get_Total_Size() - piece_offset)

            # Read Piece Data From Files
            piece_data = b''
            current_offset = 0

            for file_info in self.metadata.Files:
                file_path = self.download_dir / file_info.Path if self.download_dir else file_info.Path
                file_start = current_offset
                file_end = current_offset + file_info.Length

                # Check If This Piece Overlaps With The File
                piece_start = piece_offset
                piece_end = piece_offset + piece_size

                if piece_start < file_end and piece_end > file_start:
                    # Calculate Overlap
                    overlap_start = max(piece_start, file_start)
                    overlap_end = min(piece_end, file_end)

                    if overlap_start < overlap_end:
                        # Read From File
                        if file_path.exists():
                            with open(file_path, 'rb') as f:
                                f.seek(overlap_start - file_start)
                                data = f.read(overlap_end - overlap_start)
                                piece_data += data

                current_offset += file_info.Length

            # Verify Piece Data
            if len(piece_data) == piece_size:
                # Calculate SHA-256 Hash
                piece_hash = hashlib.sha256(piece_data).digest()
                expected_hash = bytes.fromhex(self.metadata.Piece_Hashes[piece_index])

                return piece_hash == expected_hash
            else:
                return False

        except Exception as e:
            logger.debug(f"Error Verifying Piece {piece_index} From Files: {e}")
            return False

    async def start_seeding_server(self, port: int = 6881):
        """Start Listening For Incoming Peer Connections For Seeding"""
        try:
            import asyncio
            server = await asyncio.start_server(
                self._handle_incoming_peer,
                '0.0.0.0',
                port
            )

            logger.info(f"Seeding Server Started On Port {port}")

            async with server:
                await server.serve_forever()

        except Exception as e:
            logger.error(f"Error Starting Seeding Server: {e}")
            raise

    async def _handle_incoming_peer(self, reader, writer):
        """Handle Incoming Peer Connection For Seeding"""
        peer_addr = writer.get_extra_info('peername')
        peer_id = f"{peer_addr[0]}:{peer_addr[1]}"

        logger.info(f"Incoming Peer Connection From {peer_id}")

        try:
            # Create Peer Connection Wrapper
            class IncomingPeerConnection:
                def __init__(self, reader, writer, peer_id, peer_addr):
                    self.reader = reader
                    self.writer = writer
                    self.Peer_Id = peer_id
                    self.IP = peer_addr[0]  # Extract IP address
                    self.Port = peer_addr[1]  # Extract port
                async def Send_Handshake(self, handshake: bytes) -> bool:
                    """Send BitTorrent Handshake (No Length Prefix)"""
                    try:
                        self.writer.write(handshake)
                        await self.writer.drain()
                        return True
                    except Exception as e:
                        logger.debug(f"Error Sending Handshake To {self.Peer_Id}: {e}")
                        return False

                async def Receive_Handshake(self) -> Optional[bytes]:
                    """Receive BitTorrent Handshake (No Length Prefix)"""
                    try:
                        # Receive Exactly 80 Bytes For Handshake (SHA-256 version)
                        handshake = await self.reader.readexactly(80)
                        return handshake
                    except Exception as e:
                        logger.debug(f"Error Receiving Handshake From {self.Peer_Id}: {e}")
                        return None

                async def Send_Message(self, data: bytes) -> bool:
                    try:
                        self.writer.write(data)
                        await self.writer.drain()
                        return True
                    except Exception as e:
                        logger.debug(f"Error Sending To {self.Peer_Id}: {e}")
                        return False

                async def Receive_Message(self) -> Optional[bytes]:
                    try:
                        # Read Message Length (4 Bytes)
                        length_data = await self.reader.readexactly(4)
                        length = struct.unpack('>I', length_data)[0]

                        if length == 0:
                            return length_data  # Keep-Alive

                        # Read Message Payload
                        payload = await self.reader.readexactly(length)
                        return length_data + payload
                    except Exception as e:
                        logger.debug(f"Error Receiving From {self.Peer_Id}: {e}")
                        return None

                def Close(self):
                    self.writer.close()

            peer_conn = IncomingPeerConnection(reader, writer, peer_id, peer_addr)

            # Perform HandShake
            if await self.perform_handshake(peer_conn):
                self.active_peers[peer_id] = peer_conn

                # Send OOur Bitfield
                bitfield_msg = self.create_bitfield_message()
                await peer_conn.Send_Message(bitfield_msg)

                # Start Message Handling
                await self.handle_peer_messages(peer_conn)
            else:
                peer_conn.Close()

        except Exception as e:
            logger.error(f"Error Handling Incoming Peer: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def connect_to_peers(self, peer_list: List[Tuple[str, int]]):
        """Connect To Multiple Peers With Connection Limits And Retry Logic"""
        from Peer.P2P_Communication import Peer_Connection
        
        # Limit Concurrent Connections
        max_connections = min(len(peer_list), 10)  # Max 10 concurrent connections
        
        connection_tasks = []
        for ip, port in peer_list[:max_connections]:
            peer_id = f"{ip}:{port}"
            
            # Skip If Already Connected
            if peer_id in self.active_peers:
                continue
                
            peer_conn = Peer_Connection(peer_id, ip, port)
            task = asyncio.create_task(self._connect_single_peer(peer_conn))
            connection_tasks.append(task)
        
        # Wait For All Connection Attempts
        await asyncio.gather(*connection_tasks, return_exceptions=True)
        
        logger.info(f"Connection attempts completed. Active peers: {len(self.active_peers)}")

    async def _connect_single_peer(self, peer_conn: Peer_Connection):
        """Connect To A Single Peer With Retry Logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Try To Connect
                if await peer_conn.Connect():
                    # Perform Handshake
                    if await self.perform_handshake(peer_conn):
                        self.active_peers[peer_conn.Peer_Id] = peer_conn

                        # Send Our Bitfield
                        bitfield_msg = self.create_bitfield_message()
                        await peer_conn.Send_Message(bitfield_msg)

                        # Start Message Handling For This Peer
                        asyncio.create_task(self.handle_peer_messages(peer_conn))

                        logger.info(f"Successfully Connected To Peer {peer_conn.Peer_Id}")
                        return
                
                # Connection Failed
                peer_conn.Close()
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
            except Exception as e:
                logger.debug(f"Connection attempt {attempt + 1} failed for {peer_conn.Peer_Id}: {e}")
                peer_conn.Close()
        
        logger.debug(f"Failed To Connect To Peer {peer_conn.Peer_Id} After {max_retries} Attempts")

    def get_download_progress(self) -> float:
        """Get Download Progress As Percentage"""
        if self.total_pieces == 0:
            return 100.0
        return (len(self.have_pieces) / self.total_pieces) * 100.0

    def is_complete(self) -> bool:
        """Check If Download Is Complete"""
        return len(self.have_pieces) == self.total_pieces