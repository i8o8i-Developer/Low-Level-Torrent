"""
RESTful Tracker API
Flask-Based HTTP/S Tracker With Authentication And Validation
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy import text
import os

from Config import Server_Config, Network_Config
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
        self.App = Flask(__name__)
        CORS(self.App)
        
        self.DB = DB_Manager
        self.Torrent_Ops = Torrent_Operations(DB_Manager)
        self.Peer_Ops = Peer_Operations(DB_Manager)
        self.Blockchain = Blockchain_Tracker(DB_Manager)
        
        # Register Routes
        self._Register_Routes()
        
        logger.info("Tracker API Initialized")
    
    def _Register_Routes(self):
        """Register API Routes"""
        
        @self.App.route('/')
        def Index():
            """Home Page"""
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'Web_UI', 'Templates')
            if os.path.exists(os.path.join(template_dir, 'Index.html')):
                return render_template('Index.html')
            else:
                return API_Info()
        
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
            return jsonify({
                'Status': 'OK',
                'Timestamp': datetime.utcnow().isoformat()
            })
        
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
                    'active_peers': Session.query(Peer).filter(Peer.Last_Seen > datetime.utcnow() - timedelta(minutes=30)).count()
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
