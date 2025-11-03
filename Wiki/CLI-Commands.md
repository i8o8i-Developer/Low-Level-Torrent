# CLI Commands Reference

DST Torrent Provides A Comprehensive Command-Line Interface For All Torrent Operations. This Guide Covers All Available Commands And Their Options.

## Command Structure

```bash
python Main_Client.py <command> [options]
```

## Core Commands

### Create Torrent

Create A New Torrent File From Files Or Directories.

```bash
python Main_Client.py create \
  --input <path> \
  --output <torrent_file> \
  --tracker <tracker_url> \
  [--piece-size <bytes>] \
  [--comment <text>] \
  [--private] \
  [--encrypt]
```

#### Parameters
- `--input, -i`: Source File Or Directory Path (Required)
- `--output, -o`: Output .dst Torrent File Path (Required)
- `--tracker, -t`: Tracker Announcement URL (Required)
- `--piece-size, -p`: Piece Size In Bytes (Default: 262144)
- `--comment, -c`: Torrent Comment
- `--private`: Create Private Torrent (No DHT)
- `--encrypt`: Enable Metadata Encryption

#### Examples
```bash
# Create Torrent From Single File
python Main_Client.py create -i Document.pdf -o Document.dst -t http://localhost:5043/announce

# Create Torrent From Directory
python Main_Client.py create -i /Path/To/Movies -o Movies.dst -t http://tracker.example.com/announce

# Create Encrypted Private Torrent
python Main_Client.py create -i Secret_Data -o Secret.dst -t http://secure.tracker.com/announce --private --encrypt --comment "Classified Data"
```

### Load Torrent

Load And Display Torrent Information Without Downloading.

```bash
python Main_Client.py load --torrent <torrent_file>
```

#### Parameters
- `--torrent`: Path To .dst Torrent File (Required)

#### Example Output
```
✓ Torrent Loaded Successfully!
Name: Ubuntu 22.04 ISO
Info Hash: abc123def456...
Files: 1
Total Size: 3.5 GB
Pieces: 14336
Piece Size: 256 KB
Trackers: http://tracker.ubuntu.com/announce
Comment: Ubuntu 22.04.1 LTS Desktop
Private: No
```

### Download Torrent

Download Files From A Torrent With Full P2P Support.

```bash
python Main_Client.py download \
  --torrent <torrent_file> \
  --output <download_directory> \
  [--max-peers <number>] \
  [--port <port>] \
  [--seed-after]
```

#### Parameters
- `--torrent`: Path To .dst Torrent File (Required)
- `--output, -o`: Download Directory (Required)
- `--max-peers, -m`: Maximum Concurrent Peers (Default: 10)
- `--port, -p`: Listening Port (Default: Auto)
- `--seed-after`: Continue Seeding After Download Completes

#### Examples
```bash
# Basic Download
python Main_Client.py download -t Ubuntu.dst -o Downloads/

# Download With Custom Settings
python Main_Client.py download -t Movie.dst -o Movies/ --max-peers 20 --port 6881 --seed-after
```

#### Progress Display
```
📁 Download Directory: Downloads/
📊 Total Size: 3.5 GB
🧩 Pieces: 14336

Downloading: 45.2% │████████████████████░░░░░░░░░░░░│ 45.2% (1.6 GB/3.5 GB) 2.1 MB/s ETA: 12:34
```

### Seed Torrent

Share A Completed Torrent With The Network.

```bash
python Main_Client.py seed \
  --torrent <torrent_file> \
  [--port <port>] \
  [--max-peers <number>]
```

#### Parameters
- `--torrent`: Path To .dst Torrent File (Required)
- `--port, -p`: Listening Port (Default: Auto)
- `--max-peers, -m`: Maximum Concurrent Peers (Default: 50)

#### Examples
```bash
# Start Seeding
python Main_Client.py seed -t Ubuntu.dst

# Seed With Custom Port
python Main_Client.py seed -t Ubuntu.dst --port 6882 --max-peers 100
```

### Sample Torrent

Create A Sample Torrent For Testing Purposes.

```bash
python Main_Client.py sample --output <torrent_file>
```

#### Parameters
- `--output, -o`: Output Torrent File Path (Default: Sample_Torrent.dst)

#### Example
```bash
python Main_Client.py sample -o Test_Torrent.dst
```

## Server Commands

### Start Tracker Server

```bash
python Main_Server.py [options]
```

#### Environment Variables
```bash
export SERVER_HOST=0.0.0.0
export SERVER_PORT=5043
export DEBUG_MODE=true
export ENABLE_SSL=true
export SSL_CERT_PATH=/path/to/cert.pem
export SSL_KEY_PATH=/path/to/key.pem
```

#### Command Line Options
- `--host`: Server Host (Default: 0.0.0.0)
- `--port`: Server Port (Default: 5043)
- `--debug`: Enable Debug Mode
- `--ssl`: Enable SSL/TLS

#### Examples
```bash
# Basic Server
python Main_Server.py

# Custom Configuration
SERVER_PORT=8080 DEBUG_MODE=true python Main_Server.py

# SSL Server
ENABLE_SSL=true SSL_CERT_PATH=cert.pem SSL_KEY_PATH=key.pem python Main_Server.py
```

## Advanced Commands

### Verify Torrent

Verify The Integrity Of Downloaded Files Against Torrent Hashes.

```bash
python Main_Client.py verify \
  --torrent <torrent_file> \
  --files <download_directory>
```

#### Parameters
- `--torrent`: Path To .dst Torrent File (Required)
- `--files`: Directory Containing Downloaded Files (Required)

### List Peers

Display Current Connected Peers For A Torrent.

```bash
python Main_Client.py peers --torrent <torrent_file>
```

#### Example Output
```
Connected Peers: 8
┌─────────────┬──────┬────────────┬────────────┬────────────┐
│ IP Address  │ Port │ Downloaded │ Uploaded   │ Speed      │
├─────────────┼──────┼────────────┼────────────┼────────────┤
│ 192.168.1.1 │ 6881 │ 45.2 MB    │ 12.8 MB    │ 2.1 MB/s   │
│ 10.0.0.5    │ 6882 │ 38.9 MB    │ 25.3 MB    │ 1.8 MB/s   │
│ ...         │ ...  │ ...        │ ...        │ ...        │
└─────────────┴──────┴────────────┴────────────┴────────────┘
```

### Show Statistics

Display Detailed Torrent Statistics And Performance Metrics.

```bash
python Main_Client.py stats --torrent <torrent_file>
```

#### Example Output
```
Torrent Statistics
═══════════════════════════════════════════════════════════════
Name: Ubuntu 22.04 ISO
Info Hash: abc123def456...
Size: 3.5 GB
Pieces: 14336 (256 KB each)
Completed: 45.2%

Performance Metrics
───────────────────
Download Speed: 2.1 MB/s
Upload Speed: 1.2 MB/s
Peers Connected: 8
Peers Available: 24
ETA: 12 minutes 34 seconds

Network Statistics
───────────────────
Total Downloaded: 1.6 GB
Total Uploaded: 450 MB
Connections Made: 15
Failed Connections: 2
```

## Configuration Commands

### Show Configuration

Display Current Configuration Settings.

```bash
python Main_Client.py config
```

### Validate Configuration

Check Configuration For Errors And Best Practices.

```bash
python Main_Client.py validate-config
```

## Utility Commands

### Clean Cache

Clean Temporary Files And Cache.

```bash
python Main_Client.py clean
```

### Update Tracker

Force Update Of Tracker Information.

```bash
python Main_Client.py update-tracker --torrent <torrent_file>
```

## Command Pipeline Examples

### Complete Workflow
```bash
# 1. Create Torrent
python Main_Client.py create -i MyFile.zip -o MyFile.dst -t http://localhost:5043/announce

# 2. Start Server In Background
python Main_Server.py &

# 3. Start Seeding In Background
python Main_Client.py seed -t MyFile.dst &

# 4. Download On Another Machine
python Main_Client.py download -t MyFile.dst -o Downloads/
```

### Batch Operations
```bash
# Create Multiple Torrents
for file in *.iso; do
  python Main_Client.py create -i "$file" -o "${file%.iso}.dst" -t http://tracker.com/announce
done

# Download Multiple Torrents
for torrent in *.dst; do
  python Main_Client.py download -t "$torrent" -o Downloads/ &
done
```

## Error Handling

### Common Error Messages

#### "No Peers Found"
- **Cause**: Torrent Not Being Seeded Or Tracker Unreachable
- **Solution**: Check Tracker URL And Ensure Seeder Is Running

#### "Piece Verification Failed"
- **Cause**: Corrupted Download Or Bad Torrent File
- **Solution**: Delete Partial Download And Restart

#### "Connection Refused"
- **Cause**: Firewall Blocking Ports Or Peer Offline
- **Solution**: Check Firewall Settings And Try Different Peers

#### "Disk Space Insufficient"
- **Cause**: Not Enough Free Space For Download
- **Solution**: Free Up Space Or Choose Different Download Location

### Debug Mode

Enable Verbose Logging For Troubleshooting:

```bash
DEBUG_MODE=true python Main_Client.py <command>
```

This Will Show Detailed Logs Including:
- Peer Connection Attempts
- Piece Request/Response Details
- Network Timing Information
- Error Stack Traces

## Keyboard Shortcuts

During Active Downloads/Seeding:
- `Ctrl+C`: Graceful Shutdown
- `Ctrl+Z` (Unix): Background Process
- `fg` (Unix): Bring Background Process To Foreground

## Automation Scripts

### Cron Job For Regular Seeding
```bash
# Add To crontab For Automatic Seeding
@reboot cd /path/to/Low-Level-Torrent && python Main_Client.py seed -t Important_File.dst
```

### Monitoring Script
```bash
#!/bin/bash
# monitor_torrents.sh
while true; do
  python Main_Client.py stats -t my_torrent.dst
  sleep 300  # Check every 5 minutes
done
```

This CLI Reference Covers All Major Operations. For Advanced Usage, Refer To The Source Code Documentation Or Community Forums.