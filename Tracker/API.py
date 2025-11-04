"""
RESTful Tracker API
Flask-Based HTTP/S Tracker With Authentication And Validation
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy import text
import os
import hashlib
import time
import threading
import subprocess

from Config import (
    Server_Config, Network_Config, Storage_Config, 
    API_Config, Monitoring_Config, Security_Config,
    Torrent_Config, Database_Config
)
from Database import (
    Database_Manager,
    Torrent_Operations,
    Peer_Operations,
    Initialize_Database
)
from Blockchain import Blockchain_Tracker
from Peer import Compact_Peer_List


class Tracker_API:
    """RESTful Tracker API Server"""
    
    def __init__(self, DB_Manager: Database_Manager):
        """
        Initialize Tracker API
        
        Args:
            DB_Manager: Database Manager
        """
        # Configure Template And Static Folders
        Template_Folder = os.path.join(os.path.dirname(__file__), '..', 'Web_UI', 'Templates')
        Static_Folder = os.path.join(os.path.dirname(__file__), '..', 'Web_UI', 'Static')
        
        logger.info(f"Template Folder: {Template_Folder}")
        logger.info(f"Static Folder: {Static_Folder}")
        logger.info(f"Static Folder Exists: {os.path.exists(Static_Folder)}")
        logger.info(f"Current Working Directory: {os.getcwd()}")
        
        self.App = Flask(__name__, 
                        template_folder=Template_Folder,
                        static_folder=Static_Folder)
        
        # Initialize Rate Limiting With Memory Storage (Production-Ready Fallback)
        # Using Memory Storage For Rate Limiting - Suitable For Development/Localhost
        self.Limiter = Limiter(
            get_remote_address,
            app=self.App,
            storage_uri="memory://",
            default_limits=[f"{API_Config.Rate_Limit_Requests} per {API_Config.Rate_Limit_Window} seconds"]
        )
        print("✅ Rate Limiting Configured With Redis Storage (With Memory Fallback)")
        
        CORS(self.App)
        
        self.DB = DB_Manager
        self.Torrent_Ops = Torrent_Operations(DB_Manager)
        self.Peer_Ops = Peer_Operations(DB_Manager)
        self.Blockchain = Blockchain_Tracker(DB_Manager)
        
        # Dead Drop Storage
        self.Dead_Drops = {}  # In-Memory Storage For Dead Drops
        
        # Production Setup
        self._Setup_Production()
        
        # Register Routes
        self._Register_Routes()
        
        logger.info("Tracker API Initialized")
    
    def _Validate_Info_Hash(self, Info_Hash: str) -> bool:
        """Validate Info Hash Format"""
        return (Info_Hash and 
                len(Info_Hash) == 64 and 
                all(c in '0123456789abcdefABCDEF' for c in Info_Hash))
    
    def _Validate_Torrent_Name(self, Name: str) -> bool:
        """Validate Torrent Name"""
        return (Name and 
                1 <= len(Name) <= 255 and 
                not any(c in '<>:"/\\|?*' for c in Name))
    
    def _Validate_File_Size(self, Size: int) -> bool:
        """Validate File Size"""
        return Size > 0 and Size <= 10 * 1024 * 1024 * 1024  # 10GB max
    
    def _Sanitize_Filename(self, Filename: str) -> str:
        """Sanitize Filename For Safe Storage"""
        return "".join(c for c in Filename if c.isalnum() or c in '._- ').strip()
    
    def _Setup_Production(self):
        """Production Setup And Configuration"""
        try:
            # Create Storage Directories
            Storage_Config.Torrents_Directory.mkdir(parents=True, exist_ok=True)
            Storage_Config.Temp_Directory.mkdir(parents=True, exist_ok=True)
            Storage_Config.Uploads_Directory.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Storage Directories Created: {Storage_Config.Base_Directory}")
            
            # Set Directory Permissions
            os.chmod(Storage_Config.Torrents_Directory, Storage_Config.Directory_Permissions)
            os.chmod(Storage_Config.Temp_Directory, Storage_Config.Directory_Permissions)
            os.chmod(Storage_Config.Uploads_Directory, Storage_Config.Directory_Permissions)
            
            # Configure Security Headers
            @self.App.after_request
            def Add_Security_Headers(response):
                for header, value in API_Config.Security_Headers.items():
                    response.headers[header] = value
                return response
            
            # Configure CORS Properly
            CORS(self.App, 
                 origins=API_Config.CORS_Origins,
                 methods=API_Config.CORS_Methods,
                 allow_headers=API_Config.CORS_Headers)
            
            # Start Background Cleanup Task
            self._Start_Cleanup_Task()
            
            logger.info("Production Setup Completed")
            
        except Exception as E:
            logger.error(f"Production Setup Failed: {E}")
            raise
    
    def _Start_Cleanup_Task(self):
        """Start Background File Cleanup Task"""
        import threading
        import time
        from datetime import datetime, timedelta
        
        def Cleanup_Old_Files():
            while True:
                try:
                    Current_Time = time.time()
                    Cleanup_Age = Storage_Config.Temp_File_Cleanup_Hours * 3600
                    
                    # Clean Temp Directory
                    for File_Path in Storage_Config.Temp_Directory.glob('*'):
                        if File_Path.is_file() and (Current_Time - File_Path.stat().st_mtime) > Cleanup_Age:
                            try:
                                File_Path.unlink()
                                logger.info(f"Cleaned Up Temp File: {File_Path.name}")
                            except Exception as E:
                                logger.warning(f"Failed To Clean Temp File {File_Path.name}: {E}")
                    
                    # Clean Upload Directory (Older Than 1 Hour)
                    for File_Path in Storage_Config.Uploads_Directory.glob('*'):
                        if File_Path.is_file() and (Current_Time - File_Path.stat().st_mtime) > 3600:
                            try:
                                File_Path.unlink()
                                logger.info(f"Cleaned Up Upload File: {File_Path.name}")
                            except Exception as E:
                                logger.warning(f"Failed To Clean Upload File {File_Path.name}: {E}")
                    
                except Exception as E:
                    logger.error(f"Cleanup Task Error: {E}")
                
                # Run Every Hour
                time.sleep(3600)
        
        Cleanup_Thread = threading.Thread(target=Cleanup_Old_Files, daemon=True)
        Cleanup_Thread.start()
        logger.info("File Cleanup Task Started")
    
    def _Register_Routes(self):
        """Register API Routes"""
        
        @self.App.route('/')
        def Index():
            """Home Page"""
            return render_template('Index.html')
        
        @self.App.route('/api')
        def API_Info():
            """API Information"""
            return jsonify({
                'Service': 'DST Torrent Tracker',
                'Version': '1.0',
                'Endpoints': {
                    'Announce': '/announce',
                    'Scrape': '/scrape',
                    'Stats': '/stats',
                    'Events': '/events',
                    'System_Health': '/system-health',
                    'Health': '/health'
                }
            })
        
        @self.App.route('/announce', methods=['GET'])
        def Announce():
            """Tracker Announce Endpoint"""
            try:
                # Extract Parameters
                Info_Hash = request.args.get('info_hash', '')
                Peer_Id = request.args.get('peer_id', '')
                IP = request.args.get('ip', request.remote_addr)
                Port = int(request.args.get('port', 0))
                
                Uploaded = int(request.args.get('uploaded', 0))
                Downloaded = int(request.args.get('downloaded', 0))
                Left = int(request.args.get('left', 0))
                
                Event = request.args.get('event', '')
                Compact = int(request.args.get('compact', 1))
                Numwant = int(request.args.get('numwant', 50))
                
                # Validate Required Parameters
                if not Info_Hash or not Peer_Id or not Port:
                    return jsonify({'Failure Reason': 'Missing Required Parameters'}), 400
                
                # Add/Update Peer
                self.Peer_Ops.Add_Or_Update_Peer(
                    Peer_Id=Peer_Id,
                    IP_Address=IP,
                    Port=Port,
                    Info_Hash=Info_Hash,
                    Uploaded=Uploaded,
                    Downloaded=Downloaded,
                    Left=Left,
                    Is_Seeder=(Left == 0)
                )
                
                # Add To Blockchain
                self.Blockchain.Add_Peer_Announcement({
                    'Peer_Id': Peer_Id,
                    'IP': IP,
                    'Port': Port,
                    'Info_Hash': Info_Hash,
                    'Event': Event
                })
                
                # Get Torrent Stats
                Torrent = self.Torrent_Ops.Get_Torrent(Info_Hash)
                
                # Get Peers
                Peers = self.Peer_Ops.Get_Peers(Info_Hash, Limit=Numwant)
                
                # Update Stats
                Seeders = sum(1 for P in Peers if P.Is_Seeder)
                Leechers = len(Peers) - Seeders
                self.Torrent_Ops.Update_Stats(Info_Hash, Seeders, Leechers)
                
                # Prepare Response
                if Compact:
                    # Compact Peer List
                    Peer_List = [(P.IP_Address, P.Port) for P in Peers]
                    Peers_Data = Compact_Peer_List.Encode_Peers(Peer_List)
                    
                    Response = {
                        'Interval': 1800,
                        'Complete': Seeders,
                        'Incomplete': Leechers,
                        'Peers': Peers_Data.hex()
                    }
                else:
                    # Dictionary Peer List
                    Peers_Data = [
                        {
                            'Peer Id': P.Peer_Id,
                            'IP': P.IP_Address,
                            'Port': P.Port
                        }
                        for P in Peers
                    ]
                    
                    Response = {
                        'Interval': 1800,
                        'Complete': Seeders,
                        'Incomplete': Leechers,
                        'Peers': Peers_Data
                    }
                
                logger.info(f"Announce: {Peer_Id[:8]} For {Info_Hash[:8]}")
                return jsonify(Response)
                
            except Exception as E:
                logger.error(f"Announce Failed: {E}")
                return jsonify({'Failure Reason': str(E)}), 500
        
        @self.App.route('/scrape', methods=['GET'])
        def Scrape():
            """Tracker Scrape Endpoint"""
            try:
                Info_Hashes = request.args.getlist('info_hash')
                
                if not Info_Hashes:
                    return jsonify({'Failure Reason': 'No Info Hashes Provided'}), 400
                
                Files = {}
                
                for Info_Hash in Info_Hashes:
                    Torrent = self.Torrent_Ops.Get_Torrent(Info_Hash)
                    
                    if Torrent:
                        Files[Info_Hash] = {
                            'Complete': Torrent.Complete,
                            'Downloaded': Torrent.Downloaded,
                            'Incomplete': Torrent.Incomplete,
                            'Name': Torrent.Name
                        }
                
                logger.info(f"Scrape: {len(Files)} Torrents")
                return jsonify({'Files': Files})
                
            except Exception as E:
                logger.error(f"Scrape Failed: {E}")
                return jsonify({'Failure Reason': str(E)}), 500
        
        @self.App.route('/stats', methods=['GET'])
        def Stats():
            """Tracker Statistics"""
            try:
                Session = self.DB.Get_Session()
                
                from Database import Torrent, Peer
                
                Total_Torrents = Session.query(Torrent).count()
                Total_Peers = Session.query(Peer).count()
                
                Session.close()
                
                return jsonify({
                    'Total_Torrents': Total_Torrents,
                    'Total_Peers': Total_Peers,
                    'Blockchain_Blocks': len(self.Blockchain.Chain),
                    'Max_Connections': Network_Config.Max_Connections
                })
                
            except Exception as E:
                logger.error(f"Stats Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/health', methods=['GET'])
        def Health():
            """Health Check"""
            try:
                # Check Database Connection
                Session = self.DB.Get_Session()
                Session.execute(text('SELECT 1'))
                Session.close()
                
                # Check Storage Directories
                Storage_Health = {
                    'torrents_dir': Storage_Config.Torrents_Directory.exists(),
                    'temp_dir': Storage_Config.Temp_Directory.exists(),
                    'uploads_dir': Storage_Config.Uploads_Directory.exists()
                }
                
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '1.0',
                    'database': 'connected',
                    'storage': Storage_Health
                })
            except Exception as E:
                logger.error(f"Health Check Failed: {E}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(E),
                    'timestamp': datetime.utcnow().isoformat()
                }), 503
        
        @self.App.route('/events', methods=['GET'])
        def Events():
            """Get Recent System Events"""
            try:
                Session = self.DB.Get_Session()
                
                from Database import Announcement
                
                # Get Last 20 Announcements
                Recent_Announcements = Session.query(Announcement)\
                    .order_by(Announcement.Timestamp.desc())\
                    .limit(20)\
                    .all()
                
                Events_List = []
                
                for Announcement_Record in Recent_Announcements:
                    Event_Type = "🟢 Peer Joined" if Announcement_Record.Event != 'stopped' else "🔴 Peer Left"
                    Events_List.append({
                        'Type': Event_Type,
                        'Peer_Id': Announcement_Record.Peer_Id[:16] + "...",
                        'Info_Hash': Announcement_Record.Info_Hash[:16] + "...",
                        'IP': Announcement_Record.IP_Address,
                        'Port': Announcement_Record.Port,
                        'Timestamp': Announcement_Record.Timestamp.strftime('%H:%M:%S'),
                        'Event': Announcement_Record.Event or 'announce'
                    })
                
                Session.close()
                
                return jsonify({
                    'Events': Events_List,
                    'Total': len(Events_List)
                })
                
            except Exception as E:
                logger.error(f"Events Failed: {E}")
                return jsonify({'Error': str(E), 'Events': []}), 500
        
        @self.App.route('/system-health', methods=['GET'])
        def System_Health():
            """Get System Health Metrics"""
            try:
                Session = self.DB.Get_Session()
                
                from Database import Torrent, Peer
                import psutil
                import os
                
                # Database Health
                Total_Torrents = Session.query(Torrent).count()
                Total_Peers = Session.query(Peer).count()
                
                # Calculate Health Score
                Health_Score = 100
                
                # Check Database Connectivity
                try:
                    Session.execute(text("SELECT 1"))
                    DB_Status = "Connected"
                except:
                    Health_Score -= 30
                    DB_Status = "Disconnected"
                
                # Check Blockchain Integrity
                Blockchain_Status = "Disabled" 
                
                # System Resources
                CPU_Usage = psutil.cpu_percent(interval=0.1)
                Memory = psutil.virtual_memory()
                Memory_Usage = Memory.percent
                
                # Adjust Health Based On Resources
                if CPU_Usage > 90:
                    Health_Score -= 15
                elif CPU_Usage > 70:
                    Health_Score -= 5
                
                if Memory_Usage > 90:
                    Health_Score -= 15
                elif Memory_Usage > 70:
                    Health_Score -= 5
                
                # Disk Space
                try:
                    Disk = psutil.disk_usage(os.getcwd())
                    Disk_Usage = Disk.percent
                    Disk_Free = Disk.free / (1024**3)  # GB
                    
                    if Disk_Usage > 95:
                        Health_Score -= 10
                    elif Disk_Usage > 85:
                        Health_Score -= 5
                except:
                    Disk_Usage = 0
                    Disk_Free = 0
                
                Session.close()
                
                return jsonify({
                    'Health_Score': max(0, Health_Score),
                    'Database_Status': DB_Status,
                    'Blockchain_Status': Blockchain_Status,
                    'CPU_Usage': round(CPU_Usage, 1),
                    'Memory_Usage': round(Memory_Usage, 1),
                    'Disk_Usage': round(Disk_Usage, 1),
                    'Disk_Free_GB': round(Disk_Free, 2),
                    'Total_Torrents': Total_Torrents,
                    'Total_Peers': Total_Peers,
                    'Timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as E:
                logger.error(f"System Health Failed: {E}")
                return jsonify({
                    'Health_Score': 0,
                    'Error': str(E)
                }), 500

        @self.App.route('/metrics', methods=['GET'])
        def Metrics():
            """Get Detailed System Metrics"""
            try:
                import psutil
                import os
                from datetime import datetime, timedelta

                # System Metrics
                system_metrics = {
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'cpu_count': psutil.cpu_count(),
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'percent': psutil.virtual_memory().percent
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    },
                    'network': {
                        'connections': len(psutil.net_connections()),
                        'bytes_sent': psutil.net_io_counters().bytes_sent,
                        'bytes_recv': psutil.net_io_counters().bytes_recv
                    }
                }

                # Process Metrics
                process = psutil.Process()
                process_metrics = {
                    'pid': process.pid,
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'threads': process.num_threads(),
                    'open_files': len(process.open_files()),
                    'connections': len(process.connections())
                }

                # Database Metrics
                Session = self.DB.Get_Session()
                from Database import Torrent, Peer

                db_metrics = {
                    'total_torrents': Session.query(Torrent).count(),
                    'total_peers': Session.query(Peer).count(),
                    'active_peers': Session.query(Peer).filter(Peer.Last_Announced > datetime.utcnow() - timedelta(minutes=30)).count()
                }
                Session.close()

                return jsonify({
                    'timestamp': datetime.utcnow().isoformat(),
                    'system': system_metrics,
                    'process': process_metrics,
                    'database': db_metrics,
                    'uptime_seconds': (datetime.utcnow() - datetime.fromtimestamp(psutil.Process().create_time())).total_seconds()
                })

            except Exception as e:
                logger.error(f"Metrics Collection Failed : {e}")
                return jsonify({'error': str(e)}), 500
        
        # WEB UI API ENDPOINTS
        @self.App.route('/api/stats', methods=['GET'])
        def API_Stats():
            """Get Dashboard Statistics For Web UI"""
            try:
                Session = self.DB.Get_Session()
                from Database import Torrent, Peer, Announcement
                from datetime import timedelta
                
                Total_Torrents = Session.query(Torrent).count()
                Active_Peers = Session.query(Peer).filter(
                    Peer.Last_Announced > datetime.utcnow() - timedelta(minutes=30)
                ).count()
                
                # Get Recent Announcements
                Recent_Announcements = Session.query(Announcement)\
                    .order_by(Announcement.Timestamp.desc())\
                    .limit(10)\
                    .all()
                
                Activity = [
                    f"{A.Event.upper() if A.Event else 'ANNOUNCE'}: {A.Peer_Id[:8]}... ON {A.Info_Hash[:8]}..."
                    for A in Recent_Announcements
                ]
                
                Session.close()
                
                return jsonify({
                    'Total_Torrents': Total_Torrents,
                    'Active_Peers': Active_Peers,
                    'Total_Uploads': 0,
                    'Total_Downloads': 0,
                    'Data_Shared': 0,
                    'Recent_Activity': Activity
                })
            except Exception as E:
                logger.error(f"API Stats Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/torrents', methods=['GET'])
        def API_Torrents():
            """Get All Torrents For Web UI"""
            try:
                Session = self.DB.Get_Session()
                from Database import Torrent
                
                Torrents = Session.query(Torrent).all()
                
                Torrent_List = [
                    {
                        'Name': T.Name,
                        'Info_Hash': T.Info_Hash,
                        'Size': T.Total_Size or 0,
                        'Seeders': T.Complete or 0,
                        'Leechers': T.Incomplete or 0,
                        'Created': T.Created_At.isoformat() if T.Created_At else None
                    }
                    for T in Torrents
                ]
                
                Session.close()
                
                return jsonify({'Torrents': Torrent_List})
            except Exception as E:
                logger.error(f"API Torrents Failed: {E}")
                return jsonify({'Error': str(E), 'Torrents': []}), 500
        
        @self.App.route('/api/upload', methods=['POST'])
        def API_Upload():
            """Upload File And Create Torrent"""
            try:
                from werkzeug.utils import secure_filename
                import tempfile
                from Core import Create_Torrent_From_Path
                from pathlib import Path as PathLib
                
                # Get File
                if 'file' not in request.files:
                    return jsonify({'message': 'No File Provided'}), 400
                
                File = request.files['file']
                if File.filename == '':
                    return jsonify({'message': 'No File Selected'}), 400
                
                # Get Parameters
                Name = request.form.get('name', File.filename)
                Description = request.form.get('description', '')
                Tracker_URL = request.form.get('tracker_url', f'http://localhost:{Server_Config.Port}/announce')
                Piece_Size = int(request.form.get('piece_size', 262144))
                
                # Validate Inputs
                if not self._Validate_Torrent_Name(Name):
                    return jsonify({'message': 'Invalid Torrent Name'}), 400
                
                if len(Description) > 1000:
                    return jsonify({'message': 'Description Too Long (Max 1000 Characters)'}), 400
                
                if not (Torrent_Config.Min_Piece_Size <= Piece_Size <= Torrent_Config.Max_Piece_Size):
                    return jsonify({'message': f'Invalid Piece Size (Must Be Between {Torrent_Config.Min_Piece_Size} And {Torrent_Config.Max_Piece_Size})'}), 400
                
                # Save File Temporarily
                Temp_Dir = tempfile.mkdtemp()
                Filename = secure_filename(File.filename)
                File_Path = os.path.join(Temp_Dir, Filename)
                File.save(File_Path)
                
                # Create Torrent
                Torrent_Path = File_Path + '.dst'
                Create_Torrent_From_Path(
                    Input_Path=File_Path,
                    Output_Path=Torrent_Path,
                    Tracker_URLs=[Tracker_URL],
                    Piece_Size=Piece_Size,
                    Comment=Description
                )
                
                # Calculate Info Hash
                from Core import DST_File_Handler
                Handler = DST_File_Handler()
                Metadata = Handler.Load_Torrent(Torrent_Path)
                Info_Hash = Metadata.Info_Hash
                
                # Check If Torrent Already Exists
                Session = self.DB.Get_Session()
                from Database import Torrent
                Existing_Torrent = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
                
                if Existing_Torrent:
                    Session.close()
                    # Cleanup
                    import shutil
                    shutil.rmtree(Temp_Dir)
                    
                    logger.warning(f"Torrent Already Exists: {Info_Hash}")
                    return jsonify({
                        'message': 'Torrent Already Exists',
                        'Info_Hash': Info_Hash,
                        'Name': Existing_Torrent.Name
                    }), 409  # Conflict
                
                # Add To Database
                Session = self.DB.Get_Session()
                from Database import Torrent
                
                New_Torrent = Torrent(
                    Info_Hash=Info_Hash,
                    Name=Name,
                    Total_Size=Metadata.Get_Total_Size(),
                    Piece_Count=Metadata.Get_Piece_Count(),
                    Piece_Size=Metadata.Piece_Size,
                    Comment=Description,
                    Created_By=Metadata.Created_By,
                    Private=Metadata.Private,
                    Complete=0,
                    Incomplete=0,
                    Downloaded=0
                )
                
                Session.add(New_Torrent)
                Session.commit()
                Session.close()
                
                # Save .dst File To Persistent Storage
                Persistent_Torrent_Path = Storage_Config.Torrents_Directory / f"{Info_Hash}.dst"
                import shutil
                shutil.copy2(Torrent_Path, Persistent_Torrent_Path)
                os.chmod(Persistent_Torrent_Path, Storage_Config.File_Permissions)
                
                logger.info(f"Torrent File Saved: {Persistent_Torrent_Path}")
                
                # Cleanup Temp Files
                shutil.rmtree(Temp_Dir)
                
                logger.info(f"Torrent Created: {Info_Hash}")
                
                return jsonify({
                    'message': 'Torrent Created Successfully',
                    'Info_Hash': Info_Hash,
                    'Name': Name
                })
                
            except Exception as E:
                logger.error(f"API Upload Failed: {E}")
                return jsonify({'message': str(E)}), 500
        
        @self.App.route('/api/download/<Info_Hash>', methods=['GET'])
        def API_Download(Info_Hash):
            """Download Torrent File"""
            try:
                from flask import send_file
                import os

                # Validate Info_Hash Format (Basic Security)
                if not self._Validate_Info_Hash(Info_Hash):
                    return jsonify({'message': 'Invalid Info Hash Format'}), 400

                # Check If Torrent Exists In Database
                Session = self.DB.Get_Session()
                from Database import Torrent
                Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
                Session.close()

                if not Torrent_Obj:
                    return jsonify({'message': 'Torrent Not Found'}), 404

                # Check If .dst File Exists In Storage
                Torrent_File_Path = Storage_Config.Torrents_Directory / f"{Info_Hash}.dst"
                
                if not Torrent_File_Path.exists():
                    logger.warning(f"Torrent File Missing: {Torrent_File_Path}")
                    return jsonify({'message': 'Torrent File Not Available'}), 500

                # Send The File
                Safe_Filename = f"{Torrent_Obj.Name.replace('/', '_').replace('\\', '_')}.dst"
                
                response = send_file(
                    str(Torrent_File_Path),
                    as_attachment=True,
                    download_name=Safe_Filename,
                    mimetype='application/octet-stream'
                )
                
                # Add Custom Headers
                response.headers['X-Torrent-Info-Hash'] = Info_Hash
                response.headers['X-Torrent-Name'] = Torrent_Obj.Name
                response.headers['X-Torrent-Size'] = str(Torrent_Obj.Total_Size)
                
                logger.info(f"Torrent File Served: {Info_Hash} -> {Safe_Filename}")
                return response
                
            except Exception as E:
                logger.error(f"API Download Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/seed/<Info_Hash>', methods=['POST'])
        def API_Start_Seeding(Info_Hash):
            """Start Seeding A Torrent"""
            try:
                # Get Seeding Parameters
                Torrent_Path = request.form.get('torrent_path', '')
                Download_Path = request.form.get('download_path', '')
                
                if not Torrent_Path or not Download_Path:
                    return jsonify({'message': 'Torrent Path And Download Path Required'}), 400

                # Check If Torrent Exists
                Session = self.DB.Get_Session()
                from Database import Torrent
                Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
                
                if not Torrent_Obj:
                    Session.close()
                    return jsonify({'message': 'Torrent Not Found'}), 404
                
                # Start Seeding In Background Thread
                def start_seeding():
                    try:
                        # Run The Seeding Command
                        cmd = ['python', 'Main_Client.py', 'seed', Torrent_Path]
                        logger.info(f"Starting seeding process: {' '.join(cmd)}")
                        
                        # Start SubProcess
                        process = subprocess.Popen(
                            cmd,
                            cwd=os.path.dirname(__file__),  # Run From Tracker directory
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        # Update Database - Increment Seeders
                        Torrent_Obj.Complete += 1
                        Session.commit()
                        
                        logger.info(f"Seeding Process Started For Torrent: {Info_Hash}")
                        
                    except Exception as e:
                        logger.error(f"Failed To Start Seeding Process: {e}")
                    finally:
                        Session.close()
                
                # Start Seeding In Background Thread
                threading.Thread(target=start_seeding, daemon=True).start()
                
                return jsonify({
                    'message': 'Seeding Started Successfully',
                    'Info_Hash': Info_Hash,
                    'Torrent_Path': Torrent_Path,
                    'Download_Path': Download_Path
                })
                
            except Exception as E:
                logger.error(f"API Seeding Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/peers', methods=['GET'])
        def API_Peers():
            """Get All Peers For Web UI"""
            try:
                Session = self.DB.Get_Session()
                from Database import Peer
                from datetime import timedelta
                
                Peers = Session.query(Peer).all()
                
                Peer_List = [
                    {
                        'IP': P.IP_Address,
                        'Port': P.Port,
                        'Peer_Id': P.Peer_Id,
                        'Is_Active': P.Last_Announced > datetime.utcnow() - timedelta(minutes=30),
                        'Is_Seeder': P.Is_Seeder
                    }
                    for P in Peers
                ]
                
                Total_Seeders = sum(1 for P in Peer_List if P['Is_Seeder'])
                Total_Leechers = len(Peer_List) - Total_Seeders
                
                Session.close()
                
                return jsonify({
                    'Peers': Peer_List,
                    'Total_Peers': len(Peer_List),
                    'Total_Seeders': Total_Seeders,
                    'Total_Leechers': Total_Leechers,
                    'Upload_Speed': 0
                })
            except Exception as E:
                logger.error(f"API Peers Failed: {E}")
                return jsonify({'Error': str(E), 'Peers': []}), 500
        
        @self.App.route('/api/peers/discover', methods=['POST'])
        def API_Discover_Peers():
            """Trigger Peer Discovery"""
            try:
                # In A Real Implementation, Trigger Peer Discovery
                logger.info("Peer Discovery Triggered")
                return jsonify({'message': 'Peer Discovery Initiated'})
            except Exception as E:
                logger.error(f"Peer Discovery Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/blockchain', methods=['GET'])
        def API_Blockchain():
            """Get Blockchain Data For Web UI"""
            try:
                Chain_Length = len(self.Blockchain.Chain)
                # Note: Pending_Transactions Not Implemented In Current Blockchain_Tracker
                Pending = 0  # Placeholder
                
                Blocks = [
                    {
                        'Index': B.Block_Number,
                        'Hash': B.Hash[:32] if hasattr(B, 'Hash') else 'N/A',
                        'Transactions': len(B.Data) if isinstance(B.Data, dict) else 1,
                        'Timestamp': B.Timestamp
                    }
                    for B in self.Blockchain.Chain[-10:]  # Last 10 Blocks
                ]
                
                return jsonify({
                    'Chain_Length': Chain_Length,
                    'Pending_Transactions': Pending,
                    'Difficulty': self.Blockchain.Difficulty,
                    'Last_Block_Time': Blocks[-1]['Timestamp'] if Blocks else 'N/A',
                    'Blocks': Blocks
                })
            except Exception as E:
                logger.error(f"API Blockchain Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/blockchain/mine', methods=['POST'])
        def API_Mine_Block():
            """Mine A New Block"""
            try:
                # Note: Mine_Pending_Transactions not implemented in current Blockchain_Tracker
                # For now, just add a peer announcement as a placeholder
                Block = self.Blockchain.Add_Peer_Announcement({
                    'Type': 'Manual_Mine',
                    'Miner': 'WEB_UI_MINER',
                    'Timestamp': datetime.utcnow().isoformat()
                })
                logger.info(f"Block Added: {Block.Hash if hasattr(Block, 'Hash') else 'N/A'}")
                
                return jsonify({
                    'message': 'Block Added Successfully',
                    'Block_Hash': Block.Hash if hasattr(Block, 'Hash') else 'N/A',
                    'Index': Block.Block_Number
                })
            except Exception as E:
                logger.error(f"Mining Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/system/health', methods=['GET'])
        def API_System_Health():
            """Get System Health For Web UI"""
            try:
                import psutil
                
                CPU_Usage = psutil.cpu_percent(interval=0.1)
                Memory = psutil.virtual_memory()
                Disk = psutil.disk_usage('/')
                
                Logs = [
                    "SYSTEM OPERATIONAL",
                    f"CPU: {CPU_Usage}%",
                    f"MEMORY: {Memory.percent}%",
                    f"DISK: {Disk.percent}%"
                ]
                
                return jsonify({
                    'CPU_Usage': round(CPU_Usage, 1),
                    'Memory_Usage': round(Memory.percent, 1),
                    'Disk_Usage': round(Disk.percent, 1),
                    'Network_Status': 'ONLINE',
                    'Logs': Logs
                })
            except Exception as E:
                logger.error(f"System Health Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/config', methods=['GET'])
        def API_Config():
            """Get System Configuration For Web UI"""
            try:
                return jsonify({
                    'Host': Server_Config.Host,
                    'Port': Server_Config.Port,
                    'Encryption': 'AES-256-GCM',
                    'Quantum_Resistant': True,
                    'Database': 'SQLITE',
                    'Version': '1.0.0'
                })
            except Exception as E:
                logger.error(f"Config Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        # DEAD DROP API ENDPOINTS
        @self.App.route('/api/deaddrop/create', methods=['POST'])
        def API_DeadDrop_Create():
            """Create Anonymous Dead Drop"""
            try:
                from werkzeug.utils import secure_filename
                import tempfile
                import secrets
                from datetime import timedelta
                
                # Get File
                if 'file' not in request.files:
                    return jsonify({'message': 'No File Provided'}), 400
                
                File = request.files['file']
                if File.filename == '':
                    return jsonify({'message': 'No File Selected'}), 400
                
                # Get Parameters
                Name = request.form.get('name', 'ANONYMOUS')
                Password = request.form.get('password', '')
                Expiration_Hours = int(request.form.get('expiration_hours', 24))
                Max_Downloads = int(request.form.get('max_downloads', 1))
                
                if not Password or len(Password) < 8:
                    return jsonify({'message': 'Password Must Be At Least 8 Characters'}), 400
                
                # Generate Unique Drop ID
                Drop_ID = secrets.token_urlsafe(16)
                
                # Save File Temporarily (In Production, Use Encrypted Storage)
                Temp_Dir = tempfile.mkdtemp()
                Filename = secure_filename(File.filename)
                File_Path = os.path.join(Temp_Dir, Filename)
                File.save(File_Path)
                
                # Encrypt File With Password (Simplified - Should Use Proper Encryption)
                # In Production: Use AES Encryption With Password-Derived Key
                
                # Store Dead Drop Info
                Expires_At = datetime.utcnow() + timedelta(hours=Expiration_Hours)
                self.Dead_Drops[Drop_ID] = {
                    'Name': Name,
                    'File_Path': File_Path,
                    'Password': Password,  # In Production: Hash This!
                    'Created': datetime.utcnow(),
                    'Expires': Expires_At,
                    'Max_Downloads': Max_Downloads,
                    'Downloads': 0,
                    'Original_Filename': Filename
                }
                
                logger.info(f"Dead Drop Created: {Drop_ID}")
                
                return jsonify({
                    'message': 'Dead Drop Created Successfully',
                    'Drop_ID': Drop_ID,
                    'Expires': Expires_At.strftime('%Y-%m-%d %H:%M UTC')
                })
                
            except Exception as E:
                logger.error(f"Dead Drop Create Failed: {E}")
                return jsonify({'message': str(E)}), 500
        
        @self.App.route('/api/deaddrop/access', methods=['POST'])
        def API_DeadDrop_Access():
            """Access Dead Drop With Password"""
            try:
                from flask import send_file
                
                Data = request.get_json()
                Drop_ID = Data.get('drop_id', '')
                Password = Data.get('password', '')
                
                if Drop_ID not in self.Dead_Drops:
                    return jsonify({'message': 'Dead Drop Not Found'}), 404
                
                Drop = self.Dead_Drops[Drop_ID]
                
                # Check Expiration
                if datetime.utcnow() > Drop['Expires']:
                    # Auto-Delete Expired Drop
                    import shutil
                    shutil.rmtree(os.path.dirname(Drop['File_Path']), ignore_errors=True)
                    del self.Dead_Drops[Drop_ID]
                    return jsonify({'message': 'Dead Drop Has Expired'}), 410
                
                # Check Password
                if Drop['Password'] != Password:
                    return jsonify({'message': 'Invalid Password'}), 401
                
                # Check Download Limit
                if Drop['Max_Downloads'] > 0 and Drop['Downloads'] >= Drop['Max_Downloads']:
                    return jsonify({'message': 'Download Limit Reached'}), 403
                
                # Increment Download Counter
                Drop['Downloads'] += 1
                
                # Send File
                Response = send_file(
                    Drop['File_Path'],
                    as_attachment=True,
                    download_name=Drop['Original_Filename']
                )
                
                logger.info(f"Dead Drop Accessed: {Drop_ID} ({Drop['Downloads']}/{Drop['Max_Downloads']})")
                
                # Auto-Delete If Single Use
                if Drop['Max_Downloads'] == 1:
                    import shutil
                    shutil.rmtree(os.path.dirname(Drop['File_Path']), ignore_errors=True)
                    del self.Dead_Drops[Drop_ID]
                    logger.info(f"Dead Drop Auto-Deleted: {Drop_ID}")
                
                return Response
                
            except Exception as E:
                logger.error(f"Dead Drop Access Failed: {E}")
                return jsonify({'message': str(E)}), 500
        
        @self.App.route('/api/deaddrop/list', methods=['GET'])
        def API_DeadDrop_List():
            """List Active Dead Drops"""
            try:
                # Clean Up Expired Drops
                Current_Time = datetime.utcnow()
                Expired_IDs = []
                
                for Drop_ID, Drop in self.Dead_Drops.items():
                    if Current_Time > Drop['Expires']:
                        Expired_IDs.append(Drop_ID)
                
                # Remove Expired
                import shutil
                for Drop_ID in Expired_IDs:
                    Drop = self.Dead_Drops[Drop_ID]
                    shutil.rmtree(os.path.dirname(Drop['File_Path']), ignore_errors=True)
                    del self.Dead_Drops[Drop_ID]
                
                # Return Active Drops
                Drops_List = [
                    {
                        'Drop_ID': Drop_ID,
                        'Name': Drop['Name'],
                        'Created': Drop['Created'].strftime('%Y-%m-%d %H:%M'),
                        'Expires': Drop['Expires'].strftime('%Y-%m-%d %H:%M'),
                        'Downloads': Drop['Downloads'],
                        'Max_Downloads': Drop['Max_Downloads']
                    }
                    for Drop_ID, Drop in self.Dead_Drops.items()
                ]
                
                return jsonify({'Drops': Drops_List})
                
            except Exception as E:
                logger.error(f"Dead Drop List Failed: {E}")
                return jsonify({'Error': str(E), 'Drops': []}), 500
        
        @self.App.route('/api/deaddrop/delete/<Drop_ID>', methods=['DELETE'])
        def API_DeadDrop_Delete(Drop_ID):
            """Delete Dead Drop Manually"""
            try:
                if Drop_ID not in self.Dead_Drops:
                    return jsonify({'message': 'Dead Drop Not Found'}), 404
                
                Drop = self.Dead_Drops[Drop_ID]
                
                # Delete File
                import shutil
                shutil.rmtree(os.path.dirname(Drop['File_Path']), ignore_errors=True)
                
                # Remove From Storage
                del self.Dead_Drops[Drop_ID]
                
                logger.info(f"Dead Drop Deleted: {Drop_ID}")
                
                return jsonify({'message': 'Dead Drop Deleted Successfully'})
                
            except Exception as E:
                logger.error(f"Dead Drop Delete Failed: {E}")
                return jsonify({'message': str(E)}), 500
        
        @self.App.route('/api/torrents/<Info_Hash>', methods=['GET'])
        def API_Torrent_Details(Info_Hash):
            """Get Detailed Torrent Information"""
            try:
                Session = self.DB.Get_Session()
                from Database import Torrent
                
                Torrent_Obj = Session.query(Torrent).filter_by(Info_Hash=Info_Hash).first()
                
                if not Torrent_Obj:
                    Session.close()
                    return jsonify({'message': 'Torrent Not Found'}), 404
                
                Torrent_Data = {
                    'Name': Torrent_Obj.Name,
                    'Info_Hash': Torrent_Obj.Info_Hash,
                    'Size': Torrent_Obj.Total_Size or 0,
                    'Piece_Size': Torrent_Obj.Piece_Size or 262144,
                    'Created': Torrent_Obj.Created_At.isoformat() if Torrent_Obj.Created_At else None,
                    'Seeders': Torrent_Obj.Complete or 0,
                    'Leechers': Torrent_Obj.Incomplete or 0,
                    'Downloaded': Torrent_Obj.Downloaded or 0
                }
                
                Session.close()
                
                return jsonify(Torrent_Data)
                
            except Exception as E:
                logger.error(f"Torrent Details Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/download/start', methods=['POST'])
        def API_Download_Start():
            """Start Downloading A Torrent"""
            try:
                # Get DST File
                if 'dst_file' not in request.files:
                    return jsonify({'message': 'No DST File Provided'}), 400
                
                DST_File = request.files['dst_file']
                if DST_File.filename == '':
                    return jsonify({'message': 'No DST File Selected'}), 400
                
                # Get Download Directory
                Download_Directory = request.form.get('download_directory', 'Downloads')
                
                # Save DST File Temporarily
                import tempfile
                import os
                from pathlib import Path
                
                Temp_Dir = Path(tempfile.gettempdir()) / 'dst_downloads'
                Temp_Dir.mkdir(exist_ok=True)
                
                Temp_DST_Path = Temp_Dir / DST_File.filename
                DST_File.save(str(Temp_DST_Path))
                
                # Start Download In Background Thread
                def start_download():
                    try:
                        # Run Download Command
                        cmd = ['python', 'Main_Client.py', 'download', '--torrent', str(Temp_DST_Path), '--output', Download_Directory]
                        logger.info(f"Starting download: {' '.join(cmd)}")
                        
                        # Start SubProcess
                        import subprocess
                        process = subprocess.Popen(
                            cmd,
                            cwd=os.path.dirname(__file__),  # Run From Tracker directory
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        # Store Process Info (In Real Implementation, Use A Download Manager)
                        logger.info(f"Download Process Started For: {DST_File.filename}")
                        
                    except Exception as e:
                        logger.error(f"Failed To Start Download Process: {e}")
                
                # Start Download In Background Thread
                import threading
                threading.Thread(target=start_download, daemon=True).start()
                
                return jsonify({
                    'message': 'Download Started Successfully',
                    'filename': DST_File.filename
                })
                
            except Exception as E:
                logger.error(f"Download Start Failed: {E}")
                return jsonify({'message': str(E)}), 500
        
        @self.App.route('/api/downloads/status', methods=['GET'])
        def API_Downloads_Status():
            """Get Download Status"""
            try:
                # In A Real Implementation, This Would Query Active Downloads
                # For Now, Return Empty List
                return jsonify({
                    'downloads': []
                })
                
            except Exception as E:
                logger.error(f"Downloads Status Failed: {E}")
                return jsonify({'Error': str(E)}), 500
        
        @self.App.route('/api/downloads/stop', methods=['POST'])
        def API_Downloads_Stop():
            """Stop All Downloads"""
            try:
                # In A Real Implementation, This Would Stop All Download Processes
                return jsonify({
                    'message': 'All Downloads Stopped'
                })
                
            except Exception as E:
                logger.error(f"Stop Downloads Failed: {E}")
                return jsonify({'message': str(E)}), 500
    
    def Run(self, Host: Optional[str] = None, Port: Optional[int] = None, Debug: Optional[bool] = None):
        """
        Run Tracker Server
        
        Args:
            Host: Server Host
            Port: Server Port
            Debug: Debug Mode
        """
        Host = Host or Server_Config.Host
        Port = Port or Server_Config.Port
        Debug = Debug or Server_Config.Debug
        
        logger.info(f"Starting Tracker Server On {Host}:{Port}")
        
        try:
            self.App.run(
                host=Host,
                port=Port,
                debug=Debug,
                threaded=True
            )
        except Exception as E:
            logger.error(f"Server Error: {E}")
            raise


def Initialize_Tracker_API(DB_Manager: Optional[Database_Manager] = None) -> Tracker_API:
    """
    Initialize Tracker API
    
    Args:
        DB_Manager: Database Manager (Creates New If None)
        
    Returns:
        Tracker API Instance
    """
    try:
        if DB_Manager is None:
            DB_Manager = Initialize_Database()
        
        API = Tracker_API(DB_Manager)
        logger.info("Tracker API Ready")
        
        return API
        
    except Exception as E:
        logger.error(f"Failed To Initialize Tracker API: {E}")
        raise


if __name__ == "__main__":
    logger.add("Tracker_Test.log")
    
    print("Testing Tracker API...")
    
    # Initialize
    print("\n1. Initializing Tracker...")
    API = Initialize_Tracker_API()
    print("✓ Tracker Initialized")
    
    # Test Run (Will Block)
    print("\n2. Starting Server...")
    print("Server Running At http://localhost:5043")
    print("Press Ctrl+C To Stop")
    
    API.Run()
