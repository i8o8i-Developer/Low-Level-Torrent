# DST Torrent Wiki

Welcome To The DST Torrent Wiki! This Comprehensive Documentation Covers All Aspects Of The DST Torrent System, From Basic Usage To Advanced Configuration And Development.

## Table Of Contents

### Getting Started
- [Installation And Setup](Installation-And-Setup.md)
- [CLI Commands Reference](CLI-Commands.md)

### Architecture
- [System Architecture](System-Architecture.md)

### Security
- [Cryptography Overview](Cryptography-Overview.md)

### Visual Guide
- [Visual Guide](VISUAL_GUIDE.md)

---

## About DST Torrent

DST Torrent Is A Production-Grade, Secure, And Decentralized Peer-To-Peer File Sharing System That Combines Traditional BitTorrent Protocol With Cutting-Edge Security Features And Blockchain Technology.

### Key Highlights
- **Military-Grade Security**: AES-256-GCM, RSA-4096, Quantum-Resistant Cryptography
- **Blockchain Integration**: Decentralized Peer Discovery And Immutable Tracking
- **Anti-Detection**: DPI Evasion, Traffic Obfuscation, Steganography
- **Web Interface**: Modal Popups For Interactive Details, Dead Drop Anonymous Sharing
- **Production Ready**: Health Monitoring, Metrics, Graceful Shutdown
- **Enterprise Scale**: Supports Files Up To 100TB With High Concurrency
- **Localhost Optimization**: Instant File Transfer When Source And Destination On Same Machine
- **Auto-Seeding**: Automatic Seeding Starts After Upload Completion
- **Smart Storage**: Organized Directory Structure (Storage/Uploads, Storage/Torrents, Downloads)

### Why DST Torrent?

In An Era Where Privacy And Security Are Paramount, DST Torrent Stands Out By Providing:

1. **Uncompromised Security**: Protection Against Current And Future Threats
2. **Decentralized Architecture**: No Single Point Of Failure Or Control
3. **User-Friendly Interface**: Web UI With Modal Popups And Dead Drop Sharing
4. **Enterprise-Grade Reliability**: Production-Ready With Comprehensive Monitoring
5. **Research-Focused Design**: Built For Academic And Scientific Collaboration
6. **Future-Proof Technology**: Quantum-Resistant Cryptography And Blockchain Integration
7. **Performance Optimization**: Localhost Optimization For Zero-Latency Transfers
8. **Automatic Management**: Auto-Seeding And Smart Storage Organization

### Directory Structure

```
Storage/
├── Uploads/         # Original Uploaded Files
├── Torrents/        # .dst Torrent Files And Seeding Copies
└── Temp/            # Temporary Processing Files

Downloads/           # Completed Downloaded Files
Data/                # SQLite Database Files
Logs/                # Application Log Files
```

### New Features

#### Localhost Optimization
When Both Uploader And Downloader Are On The Same Machine, DST Torrent Automatically Detects Local File Copies And Performs Instant Transfers By Copying Files Directly From Storage/Torrents To Downloads, Bypassing The P2P Protocol Entirely For Zero Network Latency.

#### Auto-Seeding
After Uploading A File Via The Web Interface, DST Torrent Automatically:
1. Saves The Original To Storage/Uploads
2. Creates A .dst Torrent In Storage/Torrents
3. Copies The File To Storage/Torrents For Seeding
4. Starts The Seeding Process In Background

---

*This Wiki Is Maintained By The DST Torrent Development Team. Contributions Are Welcome!*