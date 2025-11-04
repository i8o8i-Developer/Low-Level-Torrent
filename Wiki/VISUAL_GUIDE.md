# Web Ui Visual Guide

## WHAT YOU'VE GOT - A COMPLETE RETRO WEB INTERFACE!

---

## 🖼️ VISUAL LAYOUT

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         DST TORRENT                                      ║
║                    DIGITAL SHARING SYSTEM                                ║
║                                                        [ SYSTEM ONLINE ] ║
╚══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────┐
│ [ DASHBOARD ] [ TORRENTS ] [ UPLOAD ] [ DEAD DROP ] [ PEERS ] [ BLOCKCHAIN ] [ SYSTEM ] │
└───────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════╗
║                        SYSTEM STATISTICS                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    ║
║  │ TOTAL        │  │ ACTIVE       │  │ TOTAL        │                    ║
║  │ TORRENTS     │  │ PEERS        │  │ UPLOADS      │                    ║
║  │    0         │  │    0         │  │    0         │                    ║
║  └──────────────┘  └──────────────┘  └──────────────┘                    ║
║                                                                          ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    ║
║  │ TOTAL        │  │ DATA         │  │ SYSTEM       │                    ║
║  │ DOWNLOADS    │  │ SHARED       │  │ UPTIME       │                    ║
║  │    0         │  │   0 GB       │  │  00:00:00    │                    ║
║  └──────────────┘  └──────────────┘  └──────────────┘                    ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════╗
║                     RECENT ACTIVITY LOG                                ║
╠════════════════════════════════════════════════════════════════════════╣
║ > SYSTEM INITIALIZED                                                   ║
║ > TRACKER API STARTED                                                  ║
║ > PEER DISCOVERY ENABLED                                               ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 🎨 COLOR SCHEME

```
┌─────────────────────────────────────────────────────────┐
│                   RETRO DARK GREEN THEME                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🟢 PRIMARY GREEN:    #29b929  ▓▓▓▓▓▓▓▓▓▓▓▓▓         │
│  ⬛ DARK BACKGROUND:  #0a0e14  ▓▓▓▓▓▓▓▓▓▓▓▓▓         │
│  🟢 LIGHT GREEN TEXT: #d5e5d5  ▓▓▓▓▓▓▓▓▓▓▓▓▓         │
│  ⬜ WHITE ACCENT:     #ffffff  ▓▓▓▓▓▓▓▓▓▓▓▓▓         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📱 RESPONSIVE TABS

### DASHBOARD TAB 📊
```
╔════════════════════════════════════╗
║    SYSTEM STATISTICS               ║
║    ━━━━━━━━━━━━━━━━                ║
║    📈 Real-Time Metrics           ║
║    📊 Activity Log                ║
║    ⏱️ Auto-Refresh Every 5s       ║
╚════════════════════════════════════╝
```

### TORRENTS TAB 📁
```
╔════════════════════════════════════╗
║    TORRENT MANAGEMENT              ║
║    ━━━━━━━━━━━━━━━━                ║
║    📋 View All Torrents           ║
║    ⬇️ Download .dst Files         ║
║    🔄 Refresh List                ║
╚════════════════════════════════════╝
```

### UPLOAD TAB 📤
```
╔════════════════════════════════════╗
║    CREATE NEW TORRENT              ║
║    ━━━━━━━━━━━━━━━━                ║
║    📁 File Selection              ║
║    ✏️ Name & Description          ║
║    ⚙️ Configuration Options       ║
║    🔒 Encryption Settings         ║
║    ✅ CREATE TORRENT Button       ║
╚════════════════════════════════════╝
```

### DEAD DROP TAB 💀
```
╔════════════════════════════════════╗
║    ANONYMOUS FILE SHARING          ║
║    ━━━━━━━━━━━━━━━━                ║
║    📤 CREATE DEAD DROP            ║
║    ━━━━━━━━━━━━━━━━                ║
║    📁 File Selection              ║
║    🔑 Password Input              ║
║    ⏰ Expiration Time             ║
║    🔢 Max Downloads               ║
║    ✅ CREATE DEAD DROP Button     ║
║                                    ║
║    📥 ACCESS DEAD DROP            ║
║    ━━━━━━━━━━━━━━━━                ║
║    🆔 Drop ID Input               ║
║    🔑 Password Input              ║
║    ⬇️ ACCESS DEAD DROP Button     ║
║                                    ║
║    📋 ACTIVE DEAD DROPS           ║
║    ━━━━━━━━━━━━━━━━                ║
║    📊 Drop List                   ║
║    🔄 REFRESH LIST Button         ║
║    🗑️ DELETE Buttons              ║
╚════════════════════════════════════╝
```

### PEERS TAB 🌐
```
╔════════════════════════════════════╗
║    PEER NETWORK                    ║
║    ━━━━━━━━━━━━━━━━                ║
║    👥 Connected Peers List         ║
║    📡 Seeder/Leecher Stats         ║
║    🔍 Discover New Peers           ║
║    ⚡ Upload Speed Monitor         ║
╚════════════════════════════════════╝
```

### BLOCKCHAIN TAB ⛓️
```
╔════════════════════════════════════╗
║    BLOCKCHAIN TRACKER              ║
║    ━━━━━━━━━━━━━━━━                ║
║    🔗 Chain Length                 ║
║    📦 Pending Transactions         ║
║    ⛏️  Mine Block Button           ║
║    📜 Block History                ║
╚════════════════════════════════════╝
```

### SYSTEM TAB 🛠️
```
╔════════════════════════════════════╗
║    SYSTEM HEALTH                   ║
║    ━━━━━━━━━━━━━━━━                ║
║    💻 CPU Usage                    ║
║    🧠 Memory Usage                 ║
║    💾 Disk Usage                   ║
║    🌐 Network Status               ║
║    ⚙️  Configuration Display       ║
╚════════════════════════════════════╝
```

---

## 📋 MODAL POPUPS

### TORRENT DETAILS MODAL
```
╔══════════════════════════════════════════════════════════╗
║ ×                  TORRENT DETAILS                       ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   BASIC INFORMATION                                      ║
║   ─────────────────                                      ║
║   NAME:        MyFile.zip                                ║
║   INFO HASH:   abc123...                  [Clickable]    ║
║   SIZE:        100 MB                                    ║
║                                                          ║
║   NETWORK STATISTICS                                     ║
║   ──────────────────                                     ║
║   SEEDERS:     5                                         ║
║   LEECHERS:    2                                         ║
║                                                          ║
║   [DOWNLOAD]  [CLOSE]                                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

### PEER DETAILS MODAL
```
╔══════════════════════════════════════════════════════════╗
║ ×                  PEER DETAILS                         ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   CONNECTION INFO                                        ║
║   ───────────────                                        ║
║   IP ADDRESS:  192.168.1.100                            ║
║   PORT:        6881                                      ║
║   STATUS:      ONLINE                                    ║
║                                                          ║
║   STATISTICS                                             ║
║   ──────────                                             ║
║   DOWNLOADED:  45.2 MB                                   ║
║   UPLOADED:    12.8 MB                                   ║
║   SPEED:       2.1 MB/s                                  ║
║                                                          ║
║   [CLOSE]                                                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

### DEAD DROP SUCCESS MODAL
```
╔══════════════════════════════════════════════════════════╗
║ ×              DEAD DROP CREATED SUCCESSFULLY           ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   DROP ID:     xYz789AbC                  [Clickable]    ║
║   URL:         http://.../access          [Clickable]    ║
║   EXPIRES:     2025-11-05 12:00 UTC                     ║
║   MAX DOWNLOADS: 1                                      ║
║                                                          ║
║   ⚠️ SAVE THIS INFORMATION!                              ║
║     Information cannot be retrieved later!              ║
║                                                          ║
║   [COPY ID]  [COPY URL]  [CLOSE]                         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

### CONFIRMATION MODAL
```
╔══════════════════════════════════════════════════════════╗
║ ×                  CONFIRM ACTION                        ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   Are you sure you want to delete this Dead Drop?       ║
║                                                          ║
║   This action cannot be undone.                         ║
║                                                          ║
║   [PROCEED]  [CANCEL]                                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

## 🎮 INTERACTIVE ELEMENTS

### BUTTONS
```
┌──────────────────────┐
│ [ BUTTON TEXT ]      │  ← Bracket Style
└──────────────────────┘

TYPES:
• PRIMARY (Green Border)
• SUCCESS (Success Green)
• WARNING (Orange)
• DANGER (Red)
• SECONDARY (Light Green)
```

### STAT BOXES
```
╔════════════════════╗
║ STAT LABEL         ║
║ ━━━━━━━━━━         ║
║ 1234               ║  ← Large Number
╚════════════════════╝
```

### ACTIVITY LOG
```
╔════════════════════════════════════╗
║ > LOG ENTRY 1                      ║
║ > LOG ENTRY 2                      ║
║ > LOG ENTRY 3                      ║
╚════════════════════════════════════╝
```

### TORRENT CARD
```
╔════════════════════════════════════════════╗
║ TORRENT NAME                    [DOWNLOAD] ║
║ HASH: 1234567890abcdef...                  ║
║ SIZE: 100 MB | SEEDERS: 5 | LEECHERS: 2    ║
╚════════════════════════════════════════════╝
```

---

## 🎯 RETRO EFFECTS

### CRT SCANLINES
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ← Scanline Effect
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

### PIXEL BORDERS
```
╔══════════════════════════════╗
║                              ║  ← Thick Retro Borders
║        CONTENT               ║
║                              ║
╚══════════════════════════════╝
```

### HOVER GLOW
```
NORMAL:  [ BUTTON ]
HOVER:   [ B̲U̲T̲T̲O̲N̲ ]  ← Green Glow Effect
```

---

## 🔤 TYPOGRAPHY

### PIXEL FONT (Headers)
```
██████  ███████ ████████ 
██   ██ ██         ██    
██   ██ ███████    ██    
██   ██      ██    ██    
██████  ███████    ██    
```

### MONO FONT (Body Text)
```
SYSTEM INITIALIZED
TRACKER API STARTED
PEER DISCOVERY ENABLED
```

---

## 📐 LAYOUT STRUCTURE

### GRID SYSTEM
```
┌──────────┬──────────┬──────────┐
│  STAT 1  │  STAT 2  │  STAT 3  │
├──────────┼──────────┼──────────┤
│  STAT 4  │  STAT 5  │  STAT 6  │
└──────────┴──────────┴──────────┘
```

### PANEL LAYOUT
```
╔═══════════════════════════════════════╗
║ PANEL TITLE                           ║
╠═══════════════════════════════════════╣
║                                       ║
║           PANEL CONTENT               ║
║                                       ║
╚═══════════════════════════════════════╝
```

---

## 🎬 ANIMATIONS

### TAB SWITCHING
```
STEP 1: Click Tab Button
        ↓
STEP 2: Fade Out Current Content
        ↓
STEP 3: Fade In New Content
        ↓
STEP 4: Update Active State
```

### NOTIFICATION POPUP
```
        ┌──────────────────┐
        │ NOTIFICATION     │  ← Slides In From Right
        │ MESSAGE HERE     │
        └──────────────────┘
               ↓
        (Auto-Dismiss 5s)
```

---

## 🔧 BATCH FILES WORKFLOW

### SETUP.BAT FLOW
```
START
  ↓
CHECK PYTHON
  ↓
CREATE .venv
  ↓
ACTIVATE .venv
  ↓
UPGRADE PIP
  ↓
INSTALL PACKAGES
  ↓
SUCCESS! ✅
```

### LAUNCH_FRONTEND.BAT FLOW
```
START
  ↓
CHECK .venv
  ↓
ACTIVATE .venv
  ↓
START SERVER
  ↓
DISPLAY URLS
  ↓
SERVER RUNNING 🚀
```

---

## 🌐 API DATA FLOW

### UPLOAD TORRENT FLOW
```
USER              BROWSER           SERVER            DATABASE
  │                  │                 │                 │
  │──Select File────>│                 │                 │
  │                  │──POST /upload──>│                 │
  │                  │                 │──Save File─────>│
  │                  │                 │<─Info Hash──────│
  │                  │<─Success────────│                 │
  │<─Notification────│                 │                 │
```

### REFRESH DASHBOARD FLOW
```
TIMER            JAVASCRIPT        API              DATABASE
  │                  │               │                 │
  │──5 Seconds──────>│               │                 │
  │                  │──GET /stats──>│                 │
  │                  │               │──Query Stats───>│
  │                  │               │<─Return Data────│
  │                  │<─JSON Data────│                 │
  │                  │──Update UI───>│                 │
```

---

## 📱 RESPONSIVE BREAKPOINTS

### DESKTOP (Default)
```
╔══════════════════════════════════════════════════╗
║  [TAB1] [TAB2] [TAB3] [TAB4] [TAB5] [TAB6]      ║
║  ┌──────┬──────┬──────┬──────┬──────┬──────┐    ║
║  │STAT 1│STAT 2│STAT 3│STAT 4│STAT 5│STAT 6│    ║
║  └──────┴──────┴──────┴──────┴──────┴──────┘    ║
╚══════════════════════════════════════════════════╝
```

### TABLET (< 768px)
```
╔═══════════════════════════════════╗
║ [TAB1] [TAB2] [TAB3]              ║
║ [TAB4] [TAB5] [TAB6]              ║
║ ┌──────┬──────┬──────┐            ║
║ │STAT 1│STAT 2│STAT 3│            ║
║ ├──────┼──────┼──────┤            ║
║ │STAT 4│STAT 5│STAT 6│            ║
║ └──────┴──────┴──────┘            ║
╚═══════════════════════════════════╝
```

---

## 🎨 CSS CLASSES REFERENCE

### LAYOUT
```
.container          - Main Content Container
.panel              - Content Panel
.panel-title        - Panel Header
.stats-grid         - Statistics Grid
.activity-log       - Activity Log Container
```

### COMPONENTS
```
.tab-btn            - Tab Navigation Button
.tab-content        - Tab Content Section
.stat-box           - Statistic Display Box
.log-entry          - Log Entry Row
.btn                - Button Base Class
.form-input         - Form Input Field
```

### UTILITIES
```
.hidden             - Hide Element
.text-center        - Center Text
.mt-10              - Margin Top 10px
.mb-20              - Margin Bottom 20px
```

---

## 🎯 KEY FEATURES SUMMARY

```
✅ RETRO DARK GREEN THEME
✅ PIXELATED NON-NEON DESIGN
✅ CRT SCANLINE EFFECTS
✅ RESPONSIVE LAYOUT
✅ REAL-TIME UPDATES
✅ TORRENT MANAGEMENT
✅ PEER NETWORKING
✅ BLOCKCHAIN INTEGRATION
✅ SYSTEM MONITORING
✅ FILE UPLOAD/DOWNLOAD
✅ NOTIFICATION SYSTEM
✅ ERROR HANDLING
✅ PASCALCASE FORMATTING
✅ TWO .BAT SCRIPTS
✅ COMPREHENSIVE DOCS
```

---

## 🚀 READY TO USE!

### LAUNCH COMMANDS
```bash
# SETUP (First Time)
Setup.bat

# LAUNCH (Every Time)
Launch_Frontend.bat

# BROWSER
http://localhost:5043
```

---

## 📚 FILE REFERENCE

```
Web_UI/
├── Templates/
│   └── Index.html      → Main HTML Interface
├── Static/
│   ├── CSS/
│   │   └── Retro.css   → Retro Dark Green Theme
│   └── JS/
│       └── App.js      → Frontend JavaScript Logic
└── README.md           → Web UI Documentation

Setup.bat               → Environment Setup Script
Launch_Frontend.bat     → Server Launch Script
QUICKSTART.md           → Quick Start Guide
SUMMARY.md              → Project Summary
```

---

**🎮 YOUR RETRO WEB INTERFACE IS COMPLETE AND READY! 🟢**

```
 ██████╗ ███████╗████████╗
 ██╔══██╗██╔════╝╚══██╔══╝
 ██║  ██║███████╗   ██║   
 ██║  ██║╚════██║   ██║   
 ██████╔╝███████║   ██║   
 ╚═════╝ ╚══════╝   ╚═╝   
```

**ENJOY YOUR PIXELATED RETRO TORRENT SYSTEM! 💾🖥️🟢**
