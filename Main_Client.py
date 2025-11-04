"""
Main Client Application
CLI For Creating, Downloading, And Seeding Torrents
"""

import sys
import argparse
from pathlib import Path

# Add Parent Directory To Path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from Utils import Initialize_Logging, Format_Bytes, Progress_Bar
from Core import Create_Torrent_From_Path, DST_File_Handler
from Crypto import Initialize_Crypto_System, RSA_Handler
from Config import Torrent_Config, Paths_Config


class DST_Client:
    """DST Torrent Client"""
    
    def __init__(self):
        """Initialize Client"""
        # Initialize Logging
        Initialize_Logging()

        # Initialize Crypto
        self.Crypto = Initialize_Crypto_System()
        self.RSA = self.Crypto['RSA']

        # Seeding Control
        self.Is_Seeding = False

        # BitTorrent Protocol Instance
        self.bt_protocol = None

        # Generate Peer ID (Must Be Exactly 20 Bytes)
        import random
        peer_id_base = f"-DST{random.randint(10000, 99999)}-"
        # Pad to 20 characters with random digits
        padding_length = 20 - len(peer_id_base)
        padding = ''.join(str(random.randint(0, 9)) for _ in range(padding_length))
        self.Peer_ID = peer_id_base + padding

        logger.info("DST Client Initialized")
    
    def Create_Torrent(
        self,
        Input_Path: str,
        Output_Path: str,
        Tracker_URLs: list,
        Piece_Size: int = None,
        Comment: str = None,
        Private: bool = False
    ):
        """
        Create New Torrent
        
        Args:
            Input_Path: File Or Directory To Create Torrent From
            Output_Path: Output .dst File Path
            Tracker_URLs: List Of Tracker URLs
            Piece_Size: Custom Piece Size
            Comment: Torrent Comment
            Private: Private Torrent Flag
        """
        try:
            logger.info(f"Creating Torrent From: {Input_Path}")
            
            # Create Torrent
            Metadata = Create_Torrent_From_Path(
                Input_Path,
                Output_Path,
                Tracker_URLs,
                Piece_Size=Piece_Size,
                Comment=Comment,
                Private=Private,
                Encrypt=True
            )
            
            # Display Info
            print("\n✓ Torrent Created Successfully!")
            print(f"Name: {Metadata.Name}")
            print(f"Info Hash: {Metadata.Info_Hash}")
            print(f"Files: {len(Metadata.Files)}")
            print(f"Total Size: {Format_Bytes(Metadata.Get_Total_Size())}")
            print(f"Pieces: {Metadata.Get_Piece_Count()}")
            print(f"Piece Size: {Format_Bytes(Metadata.Piece_Size)}")
            print(f"Output: {Output_Path}")
            
            return Metadata
            
        except Exception as E:
            logger.error(f"Failed To Create Torrent: {E}")
            print(f"❌ Error: {E}")
            sys.exit(1)
    
    def Load_Torrent(self, Torrent_Path: str):
        """
        Load Torrent File
        
        Args:
            Torrent_Path: Path To .dst File
        """
        try:
            logger.info(f"Loading Torrent: {Torrent_Path}")
            
            Handler = DST_File_Handler(self.RSA)
            Metadata = Handler.Load_Torrent(Path(Torrent_Path))
            
            # Display Info
            print("\n✓ Torrent Loaded Successfully!")
            print(f"Name: {Metadata.Name}")
            print(f"Info Hash: {Metadata.Info_Hash}")
            print(f"Files: {len(Metadata.Files)}")
            print(f"Total Size: {Format_Bytes(Metadata.Get_Total_Size())}")
            print(f"Pieces: {Metadata.Get_Piece_Count()}")
            print(f"Trackers: {', '.join(Metadata.Tracker_URLs)}")
            
            return Metadata
            
        except Exception as E:
            logger.error(f"Failed To Load Torrent: {E}")
            print(f"❌ Error: {E}")
            sys.exit(1)
    
    def Download_Torrent(self, Torrent_Path: str, Output_Dir: str):
        """
        Download Torrent With Full P2P Implementation
        
        Args:
            Torrent_Path: Path To .dst File
            Output_Dir: Download Directory
        """
        import asyncio
        import time
        import requests
        import shutil
        from concurrent.futures import ThreadPoolExecutor
        
        try:
            logger.info(f"Starting Download: {Torrent_Path}")
            
            # Load Torrent
            Metadata = self.Load_Torrent(Torrent_Path)
            
            # Create Output Directory
            Output_Path = Path(Output_Dir)
            Output_Path.mkdir(parents=True, exist_ok=True)
            
            print(f"\n📁 Download Directory: {Output_Path}")
            print(f"📊 Total Size: {Format_Bytes(Metadata.Get_Total_Size())}")
            print(f"🧩 Pieces: {Metadata.Get_Piece_Count()}")
            
            # LOCALHOST OPTIMIZATION: Check If File Exists Locally In Storage/Torrents
            Project_Root = Path(__file__).parent
            Storage_Torrents = Project_Root / 'Storage' / 'Torrents'
            
            local_files_found = True
            for file_info in Metadata.Files:
                local_file_path = Storage_Torrents / file_info.Path
                if not local_file_path.exists():
                    local_files_found = False
                    break
            
            if local_files_found:
                print("🚀 Localhost Optimization: Files Found Locally, Copying Directly...")
                try:
                    for file_info in Metadata.Files:
                        source_file = Storage_Torrents / file_info.Path
                        dest_file = Output_Path / file_info.Path
                        
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(str(source_file), str(dest_file))
                        print(f"✅ Copied: {file_info.Path} ({Format_Bytes(file_info.Length)})")
                        logger.info(f"Localhost Copy: {source_file} -> {dest_file}")
                    
                    print(f"\n✅ Download Completed Successfully (Localhost Copy)!")
                    print(f"📁 Files Saved To: {Output_Path}")
                    return Metadata
                except Exception as copy_error:
                    logger.warning(f"Localhost Copy Failed, Falling Back To P2P: {copy_error}")
            
            # Initialize BitTorrent Protocol
            from Peer.BitTorrent_Protocol import BitTorrent_Protocol
            bt_protocol = BitTorrent_Protocol(Metadata, self.Peer_ID)
            bt_protocol.set_download_directory(str(Output_Path))
            
            # Get Peers From Tracker
            peers = self._get_peers_from_tracker(Metadata, port=6883)
            if not peers:
                print("❌ No Peers Found. Torrent May Not Be Available.")
                return None
            
            print(f"🔗 Found {len(peers)} Peers")
            
            # Start Download Process
            async def download_process():
                try:
                    # Connect To Peers
                    await bt_protocol.connect_to_peers(peers)
                    
                    if not bt_protocol.active_peers:
                        print("❌ Failed To Connect To Any Peers")
                        return
                    
                    print(f"✅ Connected To {len(bt_protocol.active_peers)} Peers")
                    
                    # Start Download Loop
                    start_time = time.time()
                    last_progress = 0
                    
                    while not bt_protocol.is_complete():
                        await asyncio.sleep(1)
                        
                        # Calculate Progress
                        progress = bt_protocol.get_download_progress()
                        downloaded_bytes = bt_protocol.downloaded_bytes
                        elapsed_time = time.time() - start_time
                        
                        # Calculate Speed
                        speed_bps = downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
                        
                        # Calculate ETA
                        remaining_bytes = Metadata.Get_Total_Size() - downloaded_bytes
                        eta_seconds = remaining_bytes / speed_bps if speed_bps > 0 else 0
                        
                        # Update Progress Bar
                        if progress > last_progress:
                            Progress_Bar(progress, 100, 
                                       prefix=f"Downloading: {progress:.1f}%",
                                       suffix=f"({Format_Bytes(downloaded_bytes)}/{Format_Bytes(Metadata.Get_Total_Size())}) {Format_Bytes(speed_bps)}/s ETA: {self._format_eta(eta_seconds)}")
                            last_progress = progress
                        
                        # Check For Completion
                        if bt_protocol.is_complete():
                            break
                    
                    # Download Complete
                    Progress_Bar(100, 100, 
                               prefix="Download Complete:",
                               suffix=f"({Format_Bytes(Metadata.Get_Total_Size())}) in {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
                    
                    print(f"\n✅ Download Completed Successfully!")
                    print(f"📊 Final Stats:")
                    print(f"   Downloaded: {Format_Bytes(bt_protocol.downloaded_bytes)}")
                    print(f"   Average Speed: {Format_Bytes(speed_bps)}/s")
                    print(f"   Time Elapsed: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")
                    print(f"   Peers Used: {len(bt_protocol.active_peers)}")
                    
                    return Metadata
                    
                except Exception as e:
                    logger.error(f"Download Process Error: {e}")
                    raise
            
            # Run Async Download
            try:
                asyncio.run(download_process())
            except KeyboardInterrupt:
                print("\n⏹️  Download Interrupted By User")
                return None
            
            return Metadata
            
        except Exception as E:
            logger.error(f"Failed To Download: {E}")
            print(f"❌ Error: {E}")
            sys.exit(1)
    
    def _get_peers_from_tracker(self, Metadata, left=None, event='started', port=6881):
        """
        Get Peer List From Tracker
        
        Args:
            Metadata: Torrent Metadata
            left: Bytes left to download (None for auto)
            event: Event type
            
        Returns:
            List Of (IP, Port) Tuples
        """
        import requests
        from Peer.P2P_Communication import Compact_Peer_List
        
        if left is None:
            left = Metadata.Get_Total_Size()
        
        peers = []
        
        for tracker_url in Metadata.Tracker_URLs:
            try:
                logger.info(f"Contacting Tracker: {tracker_url}")
                
                # Build Announce URL
                params = {
                    'info_hash': Metadata.Info_Hash,
                    'peer_id': self.Peer_ID,
                    'port': port,
                    'uploaded': 0,
                    'downloaded': 0,
                    'left': left,
                    'compact': 1,
                    'event': event
                }
                
                response = requests.get(tracker_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    # Parse Bencoded Response
                    import bencodepy
                    data = bencodepy.decode(response.content)
                    
                    if b'peers' in data:
                        peer_data = data[b'peers']
                        
                        # Handle Compact Format
                        if isinstance(peer_data, bytes):
                            peers.extend(Compact_Peer_List.Decode_Peers(peer_data))
                        else:
                            # Handle Dictionary Format (Less Common)
                            for peer in peer_data:
                                if b'ip' in peer and b'port' in peer:
                                    ip = peer[b'ip'].decode()
                                    port = peer[b'port']
                                    peers.append((ip, port))
                    
                    logger.info(f"Got {len(peers)} Peers From {tracker_url}")
                    break  # Use First Working Tracker
                    
            except Exception as e:
                logger.warning(f"Failed To Contact Tracker {tracker_url}: {e}")
                continue
        
        return peers
    
    def _format_eta(self, seconds):
        """
        Format ETA In Human Readable Format
        
        Args:
            seconds: ETA In Seconds
            
        Returns:
            Formatted ETA String
        """
        if seconds == 0 or seconds > 86400 * 365:  # More Than A Year
            return "Unknown"
        
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def Create_Sample_Torrent(self, output_path: str = "sample_torrent.dst"):
        """
        Create A Sample Torrent From Test Files For Testing P2P Functionality
        
        Args:
            output_path: Output .dst File Path
        """
        import os
        
        # Check If Test Files Exist
        test_file = Path("Test_Files/Sample.txt")
        if not test_file.exists():
            print("❌ Test file not found. Creating sample file...")
            # Create A Sample File For Testing
            test_file.parent.mkdir(exist_ok=True)
            with open(test_file, 'w') as f:
                f.write("This is a sample file for testing DST Torrent P2P functionality.\n" * 1000)
            print("✅ Sample file created")
        
        # Create Torrent
        tracker_urls = ["http://localhost:5043/announce"]  # Use Local Tracker
        self.Create_Torrent(
            Input_Path=str(test_file),
            Output_Path=output_path,
            Tracker_URLs=tracker_urls,
            Comment="Sample DST Torrent For Testing"
        )
        
        print(f"🎯 Sample torrent created: {output_path}")
        print("💡 You can now test downloading with: python Main_Client.py download {output_path} Downloads")
        print("💡 And seeding with: python Main_Client.py seed {output_path}")
        
        return output_path
    
    def Seed_Torrent(self, Torrent_Path: str, Port: int = 6882):
        """
        Seed Torrent With Full P2P Implementation
        
        Args:
            Torrent_Path: Path To .dst File
            Port: Port To Listen On For Incoming Connections
        """
        import asyncio
        import time
        
        try:
            logger.info(f"Starting Seeding: {Torrent_Path}")
            
            # Load Torrent
            Metadata = self.Load_Torrent(Torrent_Path)
            
            print(f"\n🌱 Seeding Mode Activated")
            print(f"📁 Torrent: {Metadata.Name}")
            print(f"🔗 Listening On Port: {Port}")
            print(f"🧩 Pieces Available: {Metadata.Get_Piece_Count()}")
            print(f"📊 Total Size: {Format_Bytes(Metadata.Get_Total_Size())}")
            print("Press Ctrl+C To Stop Seeding")
            
            # Initialize BitTorrent Protocol
            from Peer.BitTorrent_Protocol import BitTorrent_Protocol
            bt_protocol = BitTorrent_Protocol(Metadata, self.Peer_ID)
            
            # Set Download Directory (For Loading Existing Pieces)
            # Assume Torrent Files Are In Current Directory Or Subdirectories
            torrent_dir = Path(Torrent_Path).parent
            bt_protocol.set_download_directory(str(torrent_dir))
            
            # Load Existing Pieces From Files
            async def load_and_seed():
                try:
                    # Load Existing Pieces
                    await bt_protocol.load_existing_pieces()
                    
                    if not bt_protocol.have_pieces:
                        print("⚠️  No Pieces Found. Make Sure Torrent Files Exist In The Correct Location.")
                        return
                    
                    print(f"✅ Loaded {len(bt_protocol.have_pieces)}/{bt_protocol.total_pieces} Pieces")
                    
                    # Announce To Tracker
                    try:
                        announce_peers = self._get_peers_from_tracker(Metadata, left=0, event='started', port=Port)
                        logger.info(f"Announced To Tracker, Found {len(announce_peers)} Peers")
                    except Exception as e:
                        logger.warning(f"Failed To Announce To Tracker: {e}")
                    
                    # Start Seeding Server
                    seeding_task = asyncio.create_task(bt_protocol.start_seeding_server(Port))
                    
                    # Periodic Stats Update
                    uploaded_start = bt_protocol.uploaded_bytes
                    start_time = time.time()
                    
                    while True:
                        await asyncio.sleep(10)  # Update Every 10 Seconds
                        
                        elapsed = time.time() - start_time
                        uploaded_total = bt_protocol.uploaded_bytes - uploaded_start
                        upload_speed = uploaded_total / elapsed if elapsed > 0 else 0
                        
                        active_peers = len(bt_protocol.active_peers)
                        
                        print(f"\r🌱 Seeding | Peers: {active_peers} | "
                              f"Uploaded: {Format_Bytes(uploaded_total)} | "
                              f"Speed: {Format_Bytes(upload_speed)}/s | "
                              f"Time: {time.strftime('%H:%M:%S', time.gmtime(elapsed))}", 
                              end="", flush=True)
                
                except Exception as e:
                    logger.error(f"Seeding Error: {e}")
                    raise
            
            # Run Async Seeding
            try:
                asyncio.run(load_and_seed())
            except KeyboardInterrupt:
                print("\n⏹️  Seeding Stopped")
            
            return Metadata
            
        except Exception as E:
            logger.error(f"Failed To Seed: {E}")
            print(f"❌ Error: {E}")
            sys.exit(1)

    # GUI-Specific Methods

    def Create_Torrent_GUI(self, Input_Path: str, Output_Path: str, Tracker_URL: str, Comment: str = None):
        """
        Create Torrent For GUI (Single Tracker URL)
        
        Args:
            Input_Path: Input File Path
            Output_Path: Output .dst Path
            Tracker_URL: Single Tracker URL
            Comment: Torrent Comment
            
        Returns:
            bool: Success Status
        """
        try:
            self.Create_Torrent(
                Input_Path=Input_Path,
                Output_Path=Output_Path,
                Tracker_URLs=[Tracker_URL],
                Comment=Comment
            )
            return True
        except:
            return False

    def Load_Torrent_GUI(self, Torrent_Path: str):
        """
        Load Torrent For GUI
        
        Args:
            Torrent_Path: Path To .dst File
            
        Returns:
            bool: Success Status
        """
        try:
            self.Current_Metadata = self.Load_Torrent(Torrent_Path)
            return True
        except:
            return False

    def Get_Torrent_Info(self):
        """
        Get Current Torrent Information
        
        Returns:
            dict: Torrent Info
        """
        if not hasattr(self, 'Current_Metadata') or not self.Current_Metadata:
            return {}
            
        return {
            'Name': self.Current_Metadata.Name,
            'Info_Hash': self.Current_Metadata.Info_Hash,
            'Total_Size': self.Current_Metadata.Get_Total_Size(),
            'Total_Size_Formatted': Format_Bytes(self.Current_Metadata.Get_Total_Size()),
            'Piece_Count': self.Current_Metadata.Get_Piece_Count(),
            'Piece_Size': self.Current_Metadata.Piece_Size,
            'Files': len(self.Current_Metadata.Files),
            'Trackers': self.Current_Metadata.Tracker_URLs
        }

    def Download(self):
        """
        Start Download For GUI Using Full P2P Implementation

        Returns:
            bool: Success Status
        """
        import asyncio
        import threading
        
        logger.info("Download Started (GUI Mode)")

        try:
            # Get Torrent Info
            Torrent_Info = self.Get_Torrent_Info()
            if not Torrent_Info:
                logger.error("No Torrent Loaded For Download")
                return False

            # Check If Download Directory Is Set
            if not hasattr(self, 'Download_Dir') or not self.Download_Dir:
                logger.error("Download Directory Not Set")
                return False

            # Use Full Download Implementation
            def download_thread():
                try:
                    self.Download_Torrent(self.Current_Torrent_Path, self.Download_Dir)
                    print("✅ Download Completed Successfully!")
                except Exception as e:
                    logger.error(f"Download Failed: {e}")
                    print(f"❌ Download Failed: {e}")

            # Start Download In Background Thread
            thread = threading.Thread(target=download_thread, daemon=True)
            thread.start()

            return True

        except Exception as e:
            logger.error(f"Failed To Start Download: {e}")
            return False

    def Seed(self):
        """
        Start Seeding For GUI Using Full P2P Implementation

        Returns:
            bool: Success Status
        """
        import threading
        
        logger.info("Seeding Started (GUI Mode)")
        self.Is_Seeding = True

        try:
            # Get Torrent Info
            Torrent_Info = self.Get_Torrent_Info()
            if not Torrent_Info:
                logger.error("No Torrent Loaded For Seeding")
                return False

            # Use Full Seeding Implementation
            def seeding_thread():
                try:
                    self.Seed_Torrent(self.Current_Torrent_Path, Port=6881)
                except Exception as e:
                    logger.error(f"Seeding Failed: {e}")
                    print(f"❌ Seeding Failed: {e}")
                finally:
                    self.Is_Seeding = False

            # Start Seeding In Background Thread
            thread = threading.Thread(target=seeding_thread, daemon=True)
            thread.start()

            return True

        except Exception as e:
            logger.error(f"Failed To Start Seeding: {e}")
            return False

    def Stop_Seeding(self):
        """
        Stop Seeding
        """
        logger.info("Stopping Seeding...")
        self.Is_Seeding = False

    def Get_Progress(self):
        """
        Get Download Progress
        
        Returns:
            dict: Progress Info
        """
        if self.bt_protocol:
            progress = self.bt_protocol.get_download_progress()
            total_size = self.Get_Torrent_Info().get('Total_Size', 0)
            downloaded = int((progress / 100.0) * total_size) if total_size > 0 else 0
            
            return {
                'Percentage': progress,
                'Downloaded': downloaded,
                'Downloaded_Formatted': Format_Bytes(downloaded),
                'Total_Size': total_size,
                'Total_Size_Formatted': Format_Bytes(total_size),
                'Upload_Speed': 0,  # TODO: Implement Upload Speed Tracking
                'Download_Speed': 0,  # TODO: Implement Download Speed Tracking
                'Peers': len(self.bt_protocol.active_peers) if self.bt_protocol else 0
            }
        else:
            # Fallback When No BitTorrent Protocol Instance
            return {
                'Percentage': 0.0,
                'Downloaded': 0,
                'Downloaded_Formatted': '0 B',
                'Total_Size': self.Get_Torrent_Info().get('Total_Size', 0),
                'Total_Size_Formatted': self.Get_Torrent_Info().get('Total_Size_Formatted', '0 B'),
                'Upload_Speed': 0,
                'Download_Speed': 0,
                'Peers': 0
            }

    def Get_Peer_Count(self):
        """
        Get Connected Peer Count
        
        Returns:
            int: Number Of Connected Peers
        """
        if self.bt_protocol:
            return len(self.bt_protocol.active_peers)
        return 0

    def Stop_Download(self):
        """
        Stop Download
        """
        logger.info("Download Stopped (GUI Mode)")

    def Stop_Seeding(self):
        """
        Stop Seeding
        """
        logger.info("Seeding Stopped (GUI Mode)")

    def Set_Download_Directory(self, Directory: str):
        """
        Set Download Directory

        Args:
            Directory: Download Directory Path
        """
        self.Download_Dir = Directory
        # Set On BitTorrent Protocol If It Exists
        if self.bt_protocol:
            self.bt_protocol.set_download_directory(Directory)
        logger.info(f"Download Directory Set To : {Directory}")


def Main():
    """Main Client Entry Point"""
    
    # Main Parser
    Parser = argparse.ArgumentParser(
        description='DST Torrent Client - Production-Grade Torrent System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    Subparsers = Parser.add_subparsers(dest='Command', help='Commands')
    
    # Create Command
    Create_Parser = Subparsers.add_parser('create', help='Create New Torrent')
    Create_Parser.add_argument('--input', required=True, help='Input File Or Directory')
    Create_Parser.add_argument('--output', required=True, help='Output .dst File')
    Create_Parser.add_argument('--tracker', required=True, action='append', help='Tracker URL')
    Create_Parser.add_argument('--piece-size', type=int, help='Piece Size In Bytes')
    Create_Parser.add_argument('--comment', help='Torrent Comment')
    Create_Parser.add_argument('--private', action='store_true', help='Private Torrent')
    
    # Load Command
    Load_Parser = Subparsers.add_parser('load', help='Load And Display Torrent Info')
    Load_Parser.add_argument('--torrent', required=True, help='Path To .dst File')
    
    # Download Command
    Download_Parser = Subparsers.add_parser('download', help='Download Torrent')
    Download_Parser.add_argument('--torrent', required=True, help='Path To .dst File')
    Download_Parser.add_argument('--output', required=True, help='Download Directory')
    
    # Seed Command
    Seed_Parser = Subparsers.add_parser('seed', help='Seed Torrent')
    Seed_Parser.add_argument('--torrent', required=True, help='Path To .dst File')
    
    # Sample Command
    Sample_Parser = Subparsers.add_parser('sample', help='Create Sample Torrent For Testing')
    Sample_Parser.add_argument('--output', default='Sample_Torrent.dst', help='Output .dst File')
    
    # Parse Arguments
    Args = Parser.parse_args()
    
    if not Args.Command:
        Parser.print_help()
        sys.exit(1)
    
    # Initialize Client
    print("Initializing DST Torrent Client...")
    Client = DST_Client()
    
    # Execute Command
    if Args.Command == 'create':
        Client.Create_Torrent(
            Input_Path=Args.input,
            Output_Path=Args.output,
            Tracker_URLs=Args.tracker,
            Piece_Size=Args.piece_size,
            Comment=Args.comment,
            Private=Args.private
        )
    
    elif Args.Command == 'load':
        Client.Load_Torrent(Args.torrent)
    
    elif Args.Command == 'download':
        Client.Download_Torrent(Args.torrent, Args.output)
    
    elif Args.Command == 'seed':
        Client.Seed_Torrent(Args.torrent)
    
    elif Args.Command == 'sample':
        Client.Create_Sample_Torrent(Args.output)


if __name__ == "__main__":
    Main()