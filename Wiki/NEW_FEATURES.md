# New Features Update

This Document Describes The Latest Features Added To DST Torrent, Including Localhost Optimization, Auto-Seeding, And Enhanced Storage Management.

## Overview Of New Features

### ⚡ Localhost Optimization
**Zero-Latency File Transfer When Both Parties On Same Machine**

When You Upload A File And Then Download It On The Same Computer, DST Torrent Now Automatically Detects This And Performs An Instant File Copy Instead Of Using The P2P Network.

#### How It Works
1. **Detection**: When Starting A Download, Client Checks `Storage/Torrents/` Directory
2. **Verification**: Compares File Hashes Against Torrent Metadata
3. **Instant Copy**: If Valid, Uses `shutil.copy2()` For Direct Operating System Copy
4. **Destination**: Files Copied Directly To `Downloads/` Folder
5. **Fallback**: If Files Not Found Or Hashes Don't Match, Falls Back To Standard P2P Download

#### Benefits
- **Instant Transfer**: Zero Network Latency
- **No Bandwidth Usage**: Bypasses Network Stack Entirely
- **Automatic Detection**: No Configuration Required
- **Seamless Fallback**: Automatically Uses P2P If Files Not Available Locally

#### Example Scenario
```
User Uploads FliqloScr.zip Via Web Interface
↓
File Saved To Storage/Uploads/FliqloScr.zip
↓
Torrent Created In Storage/Torrents/[hash].dst
↓
Copy Made In Storage/Torrents/FliqloScr.zip (For Seeding)
↓
User Clicks "Download" On Same Machine
↓
Client Detects Local Copy In Storage/Torrents/
↓
Instant Copy To Downloads/FliqloScr.zip (0.5 Seconds)
↓
✓ Download Complete!
```

### 📁 Smart Storage Management
**Organized Directory Structure For Clear File Organization**

The New Storage Architecture Separates Files By Purpose:

```
Storage/
├── Uploads/         # Original Files Uploaded Via Web Interface
│   └── [filename]   # Preserved As-Uploaded
├── Torrents/        # Torrent Files And Seeding Copies
│   ├── [hash].dst   # Torrent Metadata Files
│   └── [filename]   # File Copies For Seeding
└── Temp/            # Temporary Processing Files
    └── [partial]    # Downloads In Progress

Downloads/           # Final Destination For Completed Downloads
    └── [filename]   # User's Downloaded Files
```

#### Directory Purposes

**Storage/Uploads/**
- Contains Original Files Uploaded Via Web Interface
- Preserved In Original State
- Used As Source For Torrent Creation
- Not Modified After Upload

**Storage/Torrents/**
- Contains .dst Torrent Metadata Files (Named By Info Hash)
- Contains File Copies Used For Seeding
- Source For Localhost Optimization
- Auto-Populated During Upload Process

**Storage/Temp/**
- Temporary Files During Processing
- Partial Downloads Before Completion
- Cleaned Up After Operations Complete

**Downloads/**
- Final Destination For All Downloaded Files
- User-Accessible Location
- Files Ready To Use After Download

### 🔄 Auto-Seeding After Upload
**Automatic Seeding Starts Immediately After File Upload**

When You Upload A File Via The Web Interface, The System Automatically Starts Seeding It For Other Users.

#### Auto-Seeding Workflow
1. **User Uploads**: File Uploaded Via Web Interface
2. **Save Original**: File Saved To `Storage/Uploads/[filename]`
3. **Create Torrent**: System Creates .dst Torrent File
4. **Save Torrent**: Torrent Saved To `Storage/Torrents/[hash].dst`
5. **Copy For Seeding**: File Copied To `Storage/Torrents/[filename]`
6. **Start Background Process**: Seeding Process Launched Using `subprocess.Popen`
7. **Update Database**: Torrent Record Marked As "Seeding"
8. **Continuous Seeding**: Process Continues In Background

#### Benefits
- **Immediate Availability**: Files Available For Download Immediately
- **No Manual Intervention**: Fully Automatic Process
- **Background Operation**: Doesn't Block Web Interface
- **Persistent Seeding**: Continues Even After Upload Complete

#### Technical Details
```python
# Subprocess Created With UTF-8 Encoding
process = subprocess.Popen(
    [python_executable, "Main_Client.py", "seed", "--torrent", torrent_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding='utf-8',
    env={'PYTHONIOENCODING': 'utf-8'}
)
```

### 🗺️ Absolute Path Support
**Cross-Platform Path Compatibility**

All File Operations Now Use Absolute Paths Based On Project Root, Ensuring Compatibility Across Different Operating Systems And File Structures.

#### Features
- **Platform Independent**: Works On Windows, Linux, MacOS
- **No Relative Path Issues**: All Paths Calculated From Project Root
- **Configurable**: Paths Can Be Changed Via Settings
- **Validation**: Path Existence Verified Before Operations

#### Path Calculation
```python
# Project Root Detection
PROJECT_ROOT = Path(__file__).parent.absolute()

# Absolute Path Construction
UPLOADS_DIR = PROJECT_ROOT / "Storage" / "Uploads"
TORRENTS_DIR = PROJECT_ROOT / "Storage" / "Torrents"
DOWNLOADS_DIR = PROJECT_ROOT / "Downloads"
```

### 🔧 Enhanced Logging And Debugging
**Comprehensive Logging For Troubleshooting**

New Extensive Logging Throughout The System For Better Debugging And Monitoring.

#### Logging Improvements
- **INFO Level For All Operations**: Download Directory, File Paths, Write Operations
- **Subprocess Output Captured**: All Stdout/Stderr Logged At INFO Level
- **UTF-8 Encoding**: Proper Handling Of Unicode Characters In Logs
- **Detailed Error Context**: Full Stack Traces And Error Messages

#### Example Log Output
```
[INFO] Download Directory (Absolute): C:\Users\...\Downloads
[INFO] File Paths In Torrent: ['FliqloScr.zip']
[INFO] Writing Piece 0 To Files
[INFO] Successfully Wrote 32290 Bytes To C:\Users\...\Downloads\FliqloScr.zip
[INFO] Auto-Seeding Started For Torrent: FliqloScr.zip
```

## Usage Examples

### Example 1: Upload And Download On Same Machine

```bash
# Step 1: Start Server
python Main_Server.py

# Step 2: Open Web Browser
# Navigate To http://localhost:5043

# Step 3: Upload File
# Click "Upload File" Button
# Select File (e.g., FliqloScr.zip)
# Wait For Upload To Complete

# Step 4: Download (Same Machine)
# Click On Uploaded Torrent
# Click "Download" Button
# File Appears In Downloads/ Instantly (Localhost Optimization)
```

### Example 2: CLI Upload With Auto-Seeding

```bash
# Create Torrent And Copy To Storage/Torrents/
python Main_Client.py create -i MyFile.zip -o Storage/Torrents/MyFile.dst -t http://localhost:5043/announce

# Copy File To Storage/Torrents/ For Seeding
cp MyFile.zip Storage/Torrents/

# Start Seeding (Manual If Not Using Web Interface)
python Main_Client.py seed --torrent Storage/Torrents/MyFile.dst
```

### Example 3: P2P Download From Remote Peer

```bash
# Download When File Not Available Locally
python Main_Client.py download -t RemoteFile.dst -o Downloads/

# Output:
# Localhost Optimization: Checking Storage/Torrents/...
# ✗ Not Found Locally, Starting P2P Download
# Connecting To Peers...
# Downloading: 45.2% │████████████░░░░│ 2.1 MB/s ETA: 12:34
```

## Configuration

### Directory Configuration Via Web Interface

1. Navigate To Settings Tab
2. Locate Directory Configuration Section
3. Paths Are Displayed (Auto-Populated From API):
   - Upload Directory: `Storage/Uploads`
   - Torrent Directory: `Storage/Torrents`
   - Download Directory: `Downloads`
   - Temp Directory: `Storage/Temp`

### Environment Variables

```bash
# Override Default Directories
export UPLOAD_DIR=/custom/uploads
export TORRENT_DIR=/custom/torrents
export DOWNLOAD_DIR=/custom/downloads
export TEMP_DIR=/custom/temp
```

## Troubleshooting

### Issue: Downloaded Files Not Appearing In Downloads/

**Solution**: Check That Localhost Optimization Is Working
```bash
# Verify Files Exist In Storage/Torrents/
ls Storage/Torrents/

# Check Logs For Copy Operations
tail -f Logs/Client.log | grep "Successfully Wrote"
```

### Issue: Auto-Seeding Not Starting

**Solution**: Check Subprocess Creation
```bash
# Verify Python Executable Path
python -c "import sys; print(sys.executable)"

# Check For Seeding Processes
ps aux | grep "Main_Client.py seed"
```

### Issue: UTF-8 Encoding Errors In Logs

**Solution**: Ensure PYTHONIOENCODING Is Set
```bash
export PYTHONIOENCODING=utf-8
python Main_Server.py
```

## Performance Characteristics

### Localhost Optimization Performance

| Scenario | Traditional P2P | Localhost Optimization | Improvement |
|----------|----------------|----------------------|-------------|
| 1 MB File | 2-5 Seconds | 0.1 Seconds | 20-50x Faster |
| 10 MB File | 10-30 Seconds | 0.5 Seconds | 20-60x Faster |
| 100 MB File | 2-5 Minutes | 2-3 Seconds | 40-150x Faster |
| 1 GB File | 10-30 Minutes | 15-20 Seconds | 30-120x Faster |

*Performance Based On Typical HDD/SSD Speeds And Network Conditions*

### Storage Requirements

- **Original File**: Stored In `Storage/Uploads/`
- **Seeding Copy**: Stored In `Storage/Torrents/`
- **Torrent Metadata**: ~10-100 KB Per .dst File

**Total Storage = (Original Size) + (Seeding Copy Size) + (Torrent Metadata)**

For Example: 100 MB File Requires ~200 MB Storage

## Future Enhancements

### Planned Features
- **Smart Storage Cleanup**: Automatic Deletion Of Old Files After Seeding Period
- **Deduplication**: Single Copy Shared Between Upload And Seeding Directories
- **Compression**: Optional Compression For Storage Efficiency
- **Cloud Storage Integration**: Support For Remote Storage Backends

### Optimization Opportunities
- **Symlinks**: Use Symbolic Links Instead Of File Copies (Linux/MacOS)
- **Hard Links**: Use Hard Links For Same-Drive Files (Windows)
- **Memory Mapping**: Use Memory-Mapped Files For Large File Operations

---

*This Document Is Part Of The DST Torrent Wiki. For More Information, See The [System Architecture](System-Architecture.md) Guide.*
