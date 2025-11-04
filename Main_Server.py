"""
Main Server Application
Production-Grade Server With Advanced Features
"""

import sys
import os
import signal
import time
import threading
import argparse
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add Parent Directory To Path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from Utils import Initialize_Logging
from Database import Initialize_Database
from Tracker import Initialize_Tracker_API
from Crypto import Initialize_Crypto_System
from Security import Initialize_Security_Features
from Config import Server_Config, Paths_Config


class ServerManager:
    """Advanced Server Manager With Lifecycle Management"""

    def __init__(self):
        self.start_time = None
        self.components = {}
        self.health_status = {}
        self.metrics = {}
        self.shutdown_event = threading.Event()
        self.threads = []

    def initialize_component(self, name: str, init_func, *args, **kwargs):
        """Initialize A Component With Error Handling"""
        try:
            logger.info(f"Initializing {name}...")
            component = init_func(*args, **kwargs)
            self.components[name] = component
            self.health_status[name] = {
                'status': 'healthy',
                'last_check': datetime.now(),
                'error_count': 0
            }
            logger.info(f"✓ {name} Ready")
            return component
        except Exception as e:
            logger.error(f"❌ Failed To Initialize {name}: {e}")
            self.health_status[name] = {
                'status': 'failed',
                'last_check': datetime.now(),
                'error': str(e),
                'error_count': 1
            }
            raise

    def start_background_monitoring(self):
        """Start Background Monitoring Threads"""
        # Health Check Thread
        health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        health_thread.start()
        self.threads.append(health_thread)

        # Metrics Collection Thread
        metrics_thread = threading.Thread(target=self._metrics_collector, daemon=True)
        metrics_thread.start()
        self.threads.append(metrics_thread)

    def _health_monitor(self):
        """Background Health Monitoring"""
        while not self.shutdown_event.is_set():
            try:
                self._perform_health_checks()
                self.shutdown_event.wait(30)  # Check Every 30 Seconds
            except Exception as e:
                logger.error(f"Health Monitor Error : {e}")
                time.sleep(5)

    def _perform_health_checks(self):
        """Perform Health Checks On All Components"""
        for name, component in self.components.items():
            try:
                # Component-Specific Health Checks
                if name == 'Database':
                    # Check Database Connectivity
                    from sqlalchemy import text
                    with component.Engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                elif name == 'Tracker':
                    # Check If Tracker API Is Responsive Via HTTP Health Endpoint
                    import requests
                    try:
                        # Get The Tracker Port From The Component Or Use Default
                        tracker_port = getattr(component, 'port', Server_Config.Port)
                        health_url = f"http://localhost:{tracker_port}/health"
                        response = requests.get(health_url, timeout=5)
                        if response.status_code != 200:
                            raise Exception(f"Health Check Returned Status {response.status_code}")
                    except requests.RequestException as e:
                        raise Exception(f"Tracker Health Check Failed: {e}")

                self.health_status[name].update({
                    'status': 'healthy',
                    'last_check': datetime.now(),
                    'error_count': 0
                })
            except Exception as e:
                error_count = self.health_status[name].get('error_count', 0) + 1
                self.health_status[name].update({
                    'status': 'unhealthy' if error_count > 3 else 'degraded',
                    'last_check': datetime.now(),
                    'error': str(e),
                    'error_count': error_count
                })
                logger.warning(f"Health Check Failed For {name}: {e}")

    def _metrics_collector(self):
        """Collect System And Application Metrics"""
        while not self.shutdown_event.is_set():
            try:
                # Get Metrics From Tracker API If Available
                tracker_metrics = {}
                if 'Tracker' in self.components:
                    try:
                        import requests
                        tracker_port = Server_Config.Port
                        metrics_url = f"http://localhost:{tracker_port}/metrics"
                        response = requests.get(metrics_url, timeout=5)
                        if response.status_code == 200:
                            tracker_metrics = response.json()
                    except Exception as e:
                        logger.debug(f"Could Not Get Tracker Metrics: {e}")

                # Combine Tracker Metrics With Local Metrics
                self.metrics.update({
                    'timestamp': datetime.now(),
                    'server_manager': {
                        'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                        'active_components': len([c for c in self.health_status.values() if c['status'] == 'healthy']),
                        'total_components': len(self.health_status)
                    },
                    'tracker_api': tracker_metrics,
                    'health_summary': self.get_health_status()
                })
                self.shutdown_event.wait(60)  # Collect Every Minute``
            except Exception as e:
                logger.error(f"Metrics Collection Error: {e}")
                time.sleep(5)

    def get_health_status(self) -> Dict[str, Any]:
        """Get Overall Health Status"""
        healthy_count = sum(1 for status in self.health_status.values() if status['status'] == 'healthy')
        total_count = len(self.health_status)

        overall_status = 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unhealthy'

        return {
            'overall_status': overall_status,
            'components': self.health_status,
            'healthy_count': healthy_count,
            'total_count': total_count,
            'timestamp': datetime.now()
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get Current Metrics"""
        return self.metrics

    def shutdown(self):
        """Graceful Shutdown"""
        logger.info("Initiating Graceful Shutdown...")
        self.shutdown_event.set()

        # Wait For Background Threads
        for thread in self.threads:
            thread.join(timeout=5)

        # Shutdown Components In Reverse Order
        for name in reversed(list(self.components.keys())):
            try:
                logger.info(f"Shutting Down {name}...")
                component = self.components[name]
                if hasattr(component, 'shutdown'):
                    component.shutdown()
                elif hasattr(component, 'close'):
                    component.close()
                logger.info(f"✓ {name} Shut Down")
            except Exception as e:
                logger.error(f"Error Shutting Down {name}: {e}")

        logger.info("Server Shutdown Complete")


def validate_configuration():
    """Validate Server Configuration"""
    issues = []

    # Check Required Directories
    required_dirs = [
        Paths_Config.Data_Dir,
        Paths_Config.Downloads_Dir,
        Paths_Config.Keys_Dir
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            issues.append(f"Required Directory Missing : {dir_path}")
        elif not os.access(dir_path, os.W_OK):
            issues.append(f"Directory Not Writable : {dir_path}")

    # Check Port Availability
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', Server_Config.Port))
    except OSError:
        issues.append(f"Port {Server_Config.Port} Is Already In Use")

    # Check Database Connectivity
    try:
        from Database import Initialize_Database
        from sqlalchemy import text
        db = Initialize_Database()
        with db.Engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        issues.append(f"Database Connectivity Issue : {e}")

    if issues:
        logger.error("Configuration Validation Failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        return False

    logger.info("✓ Configuration Validation Passed")
    return True


def setup_signal_handlers(server_manager: ServerManager):
    """Setup Signal Handlers For Graceful Shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received Signal {signum}, Initiating Shutdown...")
        server_manager.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Handle SIGUSR1 For Health Status (Unix Only)
    if platform.system() != 'Windows':
        def health_signal_handler(signum, frame):
            health = server_manager.get_health_status()
            logger.info(f"Health Status: {health['overall_status']} ({health['healthy_count']}/{health['total_count']} Components Healthy)")

        signal.signal(signal.SIGUSR1, health_signal_handler)


def print_banner():
    """Print Server Startup Banner"""
    print("\n" + "=" * 80)
    print("🏗️  DST TORRENT SERVER - PRODUCTION GRADE")
    print("=" * 80)
    print("🚀 Advanced Features:")
    print("  ✓ AES-256-GCM Encryption")
    print("  ✓ RSA-4096 Digital Signatures")
    print("  ✓ Quantum-Resistant Cryptography")
    print("  ✓ Blockchain-Based Tracking")
    print("  ✓ Advanced Security Features")
    print("  ✓ Real-Time Health Monitoring")
    print("  ✓ Performance Metrics")
    print("  ✓ Graceful Shutdown Handling")
    print("  ✓ Configuration Validation")
    print("=" * 80)


def Main():
    """Enhanced Main Server Entry Point"""

    # Parse Arguments
    parser = argparse.ArgumentParser(
        description='DST Torrent Tracker Server - Production Grade',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python Main_Server.py                    # Start With Default Settings
  python Main_Server.py --host 127.0.0.1  # Bind To localhost Only
  python Main_Server.py --debug            # Enable Debug Mode
  python Main_Server.py --validate-only    # Only Validate Configuration
        """
    )
    parser.add_argument('--host', type=str, default=Server_Config.Host,
                       help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=Server_Config.Port,
                       help='Server port (default: 5043)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable Debug Mode')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only Validate Configuration and Exit')
    parser.add_argument('--no-health-checks', action='store_true',
                       help='Disable Background Health Monitoring')

    args = parser.parse_args()

    # Initialize Server Manager
    server_manager = ServerManager()

    try:
        # Print Banner
        print_banner()

        # Initialize Logging First
        print("📋 Initializing Logging System...")
        Initialize_Logging()
        logger.info("Logging System Initialized")

        # Validate Configuration
        logger.info("🔍 Validating configuration...")
        if not validate_configuration():
            logger.error("Configuration validation failed. Exiting.")
            sys.exit(1)

        if args.validate_only:
            logger.info("✅ Configuration Validation Complete. Exiting.")
            return

        # Setup Signal Handlers
        setup_signal_handlers(server_manager)

        # Record Start Time
        server_manager.start_time = datetime.now()

        # Initialize Components
        logger.info("🔧 Initializing Server Components...")

        # Create Directories
        server_manager.initialize_component("Directories", Paths_Config.Create_All_Directories)

        # Initialize Cryptography
        crypto_system = server_manager.initialize_component(
            "Cryptography", Initialize_Crypto_System
        )

        # Initialize Security Features
        security_system = server_manager.initialize_component(
            "Security", Initialize_Security_Features
        )

        # Initialize Database
        db = server_manager.initialize_component(
            "Database", Initialize_Database
        )

        # Initialize Tracker API
        tracker = server_manager.initialize_component(
            "Tracker", Initialize_Tracker_API, db
        )

        # Start Background Monitoring
        if not args.no_health_checks:
            logger.info("📊 Starting Background Monitoring...")
            server_manager.start_background_monitoring()

        # Server Info
        logger.info("=" * 80)
        logger.info(f"🌐 Server Starting on {args.host}:{args.port}")
        logger.info(f"🔧 Debug Mode: {'Enabled' if args.debug else 'Disabled'}")
        logger.info(f"💚 Health Monitoring: {'Enabled' if not args.no_health_checks else 'Disabled'}")
        logger.info("=" * 80)

        # Print Health Status
        health = server_manager.get_health_status()
        logger.info(f"📈 System Health: {health['overall_status']} ({health['healthy_count']}/{health['total_count']} components)")

        # Start Server (This Will Block)
        logger.info("🚀 Starting Flask Server...")
        tracker.Run(Host=args.host, Port=args.port, Debug=args.debug)

    except KeyboardInterrupt:
        logger.info("\n🛑 Received Keyboard Interrupt, Shutting Down...")
    except Exception as e:
        logger.error(f"💥 Server Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Ensure Clean Shutdown
        server_manager.shutdown()


if __name__ == "__main__":
    Main()
