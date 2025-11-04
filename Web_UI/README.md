# DST TORRENT WEB UI

## RETRO DARK GREEN THEME - PIXELATED NON-NEON COMPUTER INTERFACE

### Overview

This Is A Complete Web-Based User Interface For The DST Torrent System. The UI Features A Retro Dark Green Theme Inspired By Old-School Computer Terminals, With A Pixelated, Non-Neon Aesthetic.

### Features

#### 🖥️ Dashboard
- **SYSTEM STATISTICS**: Real-Time Display Of Torrents, Peers, Uploads, Downloads
- **ACTIVITY LOG**: Live Feed Of System Events And Announcements
- **SYSTEM UPTIME**: Automatic Uptime Counter

#### 📁 Torrent Management
- **VIEW ALL TORRENTS**: Browse All Available Torrents With Details
- **CREATE TORRENT**: Upload Files And Create New Torrents
- **DOWNLOAD TORRENT**: Download Torrent Files By Hash
- **TORRENT DETAILS**: View Size, Seeders, Leechers, And More (Modal Popup)

#### 💀 DEAD DROP ANONYMOUS SHARING
- **CREATE DEAD DROP**: Upload Files For Anonymous, Self-Destructing Sharing
- **ACCESS DEAD DROP**: Download Files Using Drop ID And Password
- **MANAGE DEAD DROPS**: View And Delete Your Active Dead Drops

#### 🌐 Peer Network
- **PEER LIST**: View All Connected Peers With Status
- **PEER STATISTICS**: Seeders, Leechers, Upload Speed
- **PEER DISCOVERY**: Trigger Peer Discovery On Demand

#### ⛓️ Blockchain Tracker
- **BLOCKCHAIN VIEW**: See Chain Length, Pending Transactions
- **BLOCK MINING**: Mine New Blocks Directly From UI
- **BLOCK HISTORY**: View Recent Blocks With Details

#### 🛠️ System Monitoring
- **HEALTH METRICS**: CPU, Memory, Disk Usage In Real-Time
- **SYSTEM CONFIG**: View Server Configuration
- **SYSTEM LOGS**: Live System Log Display

### Design Theme

#### Color Palette
- **PRIMARY**: Dark Green (#29b929) - Bright Retro Green
- **BACKGROUND**: Very Dark (#0a0e14) - Deep Black-Blue
- **TEXT**: Light Green (#d5e5d5) - Soft Green Text
- **ACCENTS**: White (#ffffff) For Highlights

#### Typography
- **PIXEL FONT**: Press Start 2P For Headers And Titles
- **MONO FONT**: VT323 For Body Text And Data

#### Visual Effects
- **CRT SCANLINES**: Authentic CRT Monitor Effect
- **RETRO BORDERS**: Thick Pixel-Style Borders
- **HOVER EFFECTS**: Subtle Glowing Transitions
- **BRACKETS**: [ ] Style For Buttons And Navigation

### File Structure

```
Web_UI/
├── Templates/
│   └── Index.html          # MAIN HTML TEMPLATE
└── Static/
    ├── CSS/
    │   └── Retro.css       # RETRO DARK GREEN THEME
    └── JS/
        └── App.js          # FRONTEND APPLICATION LOGIC
```

### Api Endpoints

The Web UI Connects To These Backend APIs:

#### Dashboard
- `GET /api/stats` - Get Dashboard Statistics
- `GET /api/config` - Get System Configuration

#### Torrents
- `GET /api/torrents` - List All Torrents
- `POST /api/upload` - Upload File And Create Torrent
- `GET /api/download/<hash>` - Download Torrent File

#### Peers
- `GET /api/peers` - List All Peers
- `POST /api/peers/discover` - Trigger Peer Discovery

#### Blockchain
- `GET /api/blockchain` - Get Blockchain Data
- `POST /api/blockchain/mine` - Mine New Block

#### Dead Drop
- `POST /api/deaddrop/create` - Create New Dead Drop
- `POST /api/deaddrop/access` - Access Existing Dead Drop
- `GET /api/deaddrop/list` - List Your Dead Drops
- `DELETE /api/deaddrop/delete/<id>` - Delete Dead Drop

#### TORRENT DETAILS
- `GET /api/torrents/<hash>` - Get Torrent Details

### Setup Instructions

#### 1. Run Setup Script
```batch
Setup.bat
```
This Will:
- Create A Virtual Environment (.venv)
- Upgrade Pip
- Install All Dependencies From Requirements.txt

#### 2. Launch The Web Ui
```batch
Launch_Frontend.bat
```
This Will:
- Activate The Virtual Environment
- Start The Flask Server
- Open Web UI At http://localhost:5043

#### 3. Access The Interface
Open Your Browser And Navigate To:
```
http://localhost:5043
```

### Usage Guide

#### Creating A Torrent
1. Navigate To The **[ UPLOAD ]** Tab
2. Select A File To Share
3. Enter Torrent Name And Description
4. Configure Piece Size And Encryption
5. Click **CREATE TORRENT**
6. Wait For Processing
7. Torrent Will Appear In **[ TORRENTS ]** Tab

#### Downloading A Torrent
1. Navigate To The **[ TORRENTS ]** Tab
2. Find The Torrent You Want
3. Click **DOWNLOAD** Button
4. Torrent File Will Download To Your Computer

#### Monitoring Peers
1. Navigate To The **[ PEERS ]** Tab
2. View All Connected Peers
3. Click **DISCOVER PEERS** To Find New Peers
4. View Seeder/Leecher Statistics

#### Blockchain Operations
1. Navigate To The **[ BLOCKCHAIN ]** Tab
2. View Chain Statistics
3. Click **MINE BLOCK** To Mine A New Block
4. View Block History

#### System Monitoring
1. Navigate To The **[ SYSTEM ]** Tab
2. Monitor CPU, Memory, Disk Usage
3. View System Configuration
4. Check System Logs

#### Creating A Dead Drop
1. Navigate To The **[ DEAD DROP ]** Tab
2. Select A File To Share Anonymously
3. Enter A Strong Password (Minimum 8 Characters)
4. Choose Expiration Time (1 Hour To 7 Days)
5. Set Max Downloads (1 For Single Use, Unlimited For Public)
6. Click **CREATE DEAD DROP**
7. Save The Drop ID And Access URL From The Success Modal
8. Share Drop ID And Password Through Separate Channels

#### Accessing A Dead Drop
1. Navigate To The **[ DEAD DROP ]** Tab
2. Scroll To **ACCESS DEAD DROP** Section
3. Enter The Drop ID Received From Sender
4. Enter The Password Received Separately
5. Click **ACCESS DEAD DROP**
6. File Will Download Automatically If Valid

#### Managing Dead Drops
1. In **[ DEAD DROP ]** Tab, Scroll To **ACTIVE DEAD DROPS**
2. Click **REFRESH LIST** To Update
3. View Expiration Times And Download Counts
4. Click **DELETE** To Manually Remove A Drop

### Pascalcase Formatting

All Text, Code, Comments, File Names, And Folder Names Follow PascalCase Convention:
- **Files**: `Index.html`, `App.js`, `Retro.css`
- **Folders**: `Web_UI`, `Templates`, `Static`
- **Variables**: `Total_Torrents`, `Active_Peers`
- **Functions**: `Refresh_Dashboard()`, `Handle_Upload()`
- **HTML IDs**: `Torrent_List`, `Upload_Form`
- **CSS Classes**: `.panel-title`, `.stat-box`

### Technical Details

#### Frontend Technologies
- **HTML5**: Semantic Markup
- **CSS3**: Custom Retro Theme With CRT Effects
- **VANILLA JAVASCRIPT**: No External Libraries
- **FETCH API**: RESTful API Communication

#### Backend Technologies
- **FLASK**: Python Web Framework
- **FLASK-CORS**: Cross-Origin Resource Sharing
- **SQLALCHEMY**: Database ORM
- **LOGURU**: Logging System

#### Features
- **REAL-TIME UPDATES**: Auto-Refresh Every 5 Seconds
- **RESPONSIVE DESIGN**: Works On Desktop And Tablet
- **NOTIFICATION SYSTEM**: Toast Notifications For User Actions
- **ERROR HANDLING**: Graceful Error Messages
- **PROGRESS TRACKING**: Upload Progress Display

### Customization

#### Changing Theme Colors
Edit `Web_UI/Static/CSS/Retro.css`:
```css
:root {
    --color-primary: #29b929;      /* BRIGHT GREEN */
    --color-bg-primary: #0a0e14;   /* DARK BACKGROUND */
    /* MODIFY OTHER COLORS AS NEEDED */
}
```

#### Changing Auto-Refresh Interval
Edit `Web_UI/Static/JS/App.js`:
```javascript
function Start_Auto_Refresh() {
    // CHANGE 5000 TO DESIRED MILLISECONDS
    Refresh_Interval = setInterval(() => {
        // ...
    }, 5000);
}
```

#### Adding New Tabs
1. Add Tab Button In HTML
2. Add Tab Content Section
3. Create Switch Case In `Switch_Tab()` Function
4. Implement Data Loading Function

### Troubleshooting

#### Port Already In Use
If Port 5043 Is Already In Use:
1. Edit `Config/Settings.py`
2. Change `Server_Config.Port` Value
3. Restart Server

#### Virtual Environment Issues
If Virtual Environment Fails:
1. Delete `.venv` Folder
2. Run `Setup.bat` Again
3. Ensure Python 3.8+ Is Installed

#### Database Errors
If Database Errors Occur:
1. Check `Data/` Folder Exists
2. Ensure Write Permissions
3. Delete `Torrent_System.db` And Restart

#### Styling Issues
If CSS Not Loading:
1. Clear Browser Cache
2. Check `Web_UI/Static/CSS/Retro.css` Exists
3. Verify Flask Template/Static Paths

### Development

#### Project Structure
```
DST_Torrent/
├── Web_UI/                 # WEB INTERFACE
│   ├── Templates/         # HTML TEMPLATES
│   └── Static/            # CSS AND JAVASCRIPT
├── Tracker/               # API SERVER
├── Core/                  # TORRENT LOGIC
├── Crypto/                # ENCRYPTION
├── Database/              # DATA MODELS
├── Setup.bat              # SETUP SCRIPT
└── Launch_Frontend.bat    # LAUNCH SCRIPT
```

#### Adding New Api Endpoints
1. Edit `Tracker/API.py`
2. Add Route Function In `_Register_Routes()`
3. Implement Logic
4. Update JavaScript In `App.js`
5. Update HTML If Needed

### Security Notes

⚠️ **IMPORTANT SECURITY CONSIDERATIONS**:

1. **PRODUCTION DEPLOYMENT**: Change `Server_Config.Secret_Key` In Production
2. **FILE UPLOADS**: Implement Size Limits And File Type Validation
3. **API AUTHENTICATION**: Add Authentication For Production Use
4. **HTTPS**: Use HTTPS In Production Environments
5. **INPUT VALIDATION**: All User Inputs Are Validated Server-Side

### License

This Project Is Licensed Under The MIT License.

### Credits

**DEVELOPER**: I8O8I-DEVELOPER  
**PROJECT**: DST TORRENT - DIGITAL SHARING SYSTEM  
**THEME**: RETRO DARK GREEN PIXELATED NON-NEON  
**YEAR**: 2025

### Support

For Issues And Support:
- **GITHUB**: Report Issues On Project Repository
- **DOCUMENTATION**: See Main README.md For Full Documentation

---

**ENJOY YOUR RETRO-THEMED TORRENT EXPERIENCE!** 🟢💾🖥️
