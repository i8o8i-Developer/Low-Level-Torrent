# System Architecture

This Document Describes The High-Level Architecture Of DST Torrent, Including Component Relationships, Data Flow, And Design Principles.

## Overview

DST Torrent Is Built As A Modular, Production-Grade P2P File Sharing System With Emphasis On Security, Scalability, And Decentralization.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DST Torrent Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Application │  │   Core      │  │  Security   │  │ Blockchain  │         │
│  │   Layer     │  │   Layer     │  │   Layer     │  │   Layer     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Network   │  │  Storage    │  │ Monitoring  │  │  Config     │         │
│  │   Layer     │  │   Layer     │  │   Layer     │  │   Layer     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Application Layer

#### Main_Server.py
- **Purpose**: Production-Grade Tracker Server
- **Features**:
  - HTTP/HTTPS RESTful API
  - Health Monitoring And Metrics
  - Graceful Shutdown Handling
  - Multi-Threaded Request Processing
- **Responsibilities**:
  - Peer Discovery And Coordination
  - Torrent Statistics Tracking
  - API Rate Limiting
  - Background Health Checks

#### Main_Client.py
- **Purpose**: CLI Client For Torrent Operations
- **Features**:
  - Command-Line Interface
  - Full P2P Download/Upload Support
  - Progress Tracking With Real-Time Updates
  - Error Recovery And Retry Logic
- **Responsibilities**:
  - Torrent Creation And Loading
  - P2P Download Management
  - Seeding Operations
  - User Interaction Handling

#### Web_UI/
- **Purpose**: Web-Based User Interface
- **Features**:
  - Modal Popup System For Interactive Details
  - Dead Drop Anonymous File Sharing
  - Real-Time Dashboard And Monitoring
  - RESTful API Integration
- **Components**:
  - `Index.html`: Main Interface Template
  - `App.js`: Frontend Application Logic
  - `Retro.css`: Styling And Themes

### 2. Core Layer

#### Torrent_Metadata.py
- **Purpose**: Torrent File Handling And Metadata Management
- **Features**:
  - Bencode Format Support
  - Multi-File Torrent Support
  - Piece Hash Verification
  - Metadata Encryption
- **Key Classes**:
  - `Torrent_Metadata`: Core Metadata Structure
  - `DST_File_Handler`: Encrypted File Operations

#### BitTorrent_Protocol.py
- **Purpose**: Complete BitTorrent Protocol Implementation
- **Features**:
  - Peer Handshake Protocol
  - Piece Selection Algorithms (Rarest-First)
  - Block Request/Response Handling
  - Connection Management
- **Key Classes**:
  - `BitTorrent_Protocol`: Main Protocol Handler
  - `Peer_Connection`: Individual Peer Management

### 3. Security Layer

#### Core_Crypto.py
- **Purpose**: Cryptographic Operations
- **Features**:
  - AES-256-GCM Encryption
  - RSA-4096 Key Pairs
  - Digital Signatures
  - Certificate Management
- **Key Classes**:
  - `AES_Cipher`: Symmetric Encryption
  - `RSA_Handler`: Asymmetric Cryptography

#### Quantum_Crypto.py
- **Purpose**: Post-Quantum Cryptography
- **Features**:
  - CRYSTALS-Kyber Key Exchange
  - Dilithium Signatures
  - Future-Proof Cryptography
- **Dependencies**: liboqs Library

#### Advanced_Security.py
- **Purpose**: Advanced Security Features
- **Features**:
  - Anti-DPI Traffic Obfuscation
  - Steganography For Data Hiding
  - Zero-Knowledge Proofs
  - Self-Destructing Torrents
- **Key Classes**:
  - `Anti_DPI_Engine`: Traffic Obfuscation
  - `Steganography_Handler`: Data Hiding

### 4. Blockchain Layer

#### Tracker.py
- **Purpose**: Decentralized Peer Discovery
- **Features**:
  - Custom Blockchain Implementation
  - Proof-Of-Work Mining
  - Immutable Transaction Ledger
  - Decentralized Consensus
- **Key Classes**:
  - `Block`: Blockchain Block Structure
  - `Blockchain`: Chain Management
  - `Proof_Of_Work`: Mining Algorithm

### 5. Network Layer

#### P2P_Communication.py
- **Purpose**: Low-Level Network Communication
- **Features**:
  - TCP Socket Management
  - Connection Pooling
  - Bandwidth Throttling
  - NAT Traversal Support
- **Key Classes**:
  - `Peer_Manager`: Connection Coordination
  - `Compact_Peer_List`: Peer List Compression

#### API.py (Tracker)
- **Purpose**: RESTful Tracker API
- **Features**:
  - HTTP/HTTPS Endpoints
  - JSON Request/Response
  - Authentication And Authorization
  - Rate Limiting
- **Endpoints**:
  - `GET /announce`: Peer Discovery
  - `POST /scrape`: Torrent Statistics
  - `GET /health`: Health Check

### 6. Storage Layer

#### Models.py (Database)
- **Purpose**: Data Persistence
- **Features**:
  - SQLite ORM With SQLAlchemy
  - Schema Migrations
  - Connection Pooling
  - Transaction Management
- **Key Models**:
  - `Torrent_Record`: Torrent Metadata
  - `Peer_Record`: Peer Information
  - `Blockchain_Record`: Block Data

### 7. Configuration Layer

#### Settings.py
- **Purpose**: Centralized Configuration
- **Features**:
  - Environment Variable Support
  - Configuration Validation
  - Dynamic Reloading
  - Default Value Management

## Data Flow Architecture

### Torrent Creation Flow

```
File/Directory Input
        │
        ▼
Torrent Metadata Creation
        │
        ▼
Piece Hash Calculation
        │
        ▼
Metadata Encryption (RSA)
        │
        ▼
DST File Output (.dst)
```

### Download Flow

```
DST File Loading
        │
        ▼
Tracker Announcement
        │
        ▼
Peer List Retrieval
        │
        ▼
Peer Connections Establishment
        │
        ▼
Piece Requests (Rarest-First)
        │
        ▼
Block Downloads (16KB)
        │
        ▼
Piece Verification (SHA-1)
        │
        ▼
File Assembly
```

### Security Flow

```
Data Input
        │
        ▼
AES-256-GCM Encryption
        │
        ▼
Traffic Obfuscation (XOR + Padding)
        │
        ▼
Protocol Masking
        │
        ▼
Secure Transmission
```

## Design Principles

### 1. Modularity
- Each Component Has Clear Responsibilities
- Loose Coupling Between Modules
- Dependency Injection Pattern
- Plugin Architecture Support

### 2. Security First
- Defense In Depth Approach
- Zero-Trust Architecture
- Cryptographic Agility
- Privacy By Design

### 3. Production Ready
- Comprehensive Error Handling
- Structured Logging
- Health Monitoring
- Graceful Degradation

### 4. Scalability
- Asynchronous Operations
- Connection Pooling
- Resource Management
- Horizontal Scaling Support

### 5. Decentralization
- Blockchain-Based Coordination
- Peer-To-Peer Communication
- No Single Point Of Failure
- Distributed Consensus

## Component Communication

### Synchronous Communication
- Direct Function Calls Within Modules
- Database Queries
- File System Operations

### Asynchronous Communication
- Network Requests (HTTP/HTTPS)
- P2P Peer Communication
- Background Health Monitoring
- Metrics Collection

### Event-Driven Architecture
- Torrent Completion Events
- Peer Connection Events
- Error Notification Events
- Health Status Changes

## Error Handling And Resilience

### Error Propagation
- Exceptions Bubble Up With Context
- Structured Error Messages
- Error Codes And Categories
- Recovery Strategies

### Fault Tolerance
- Automatic Retry Logic
- Circuit Breaker Pattern
- Graceful Degradation
- Self-Healing Components

### Monitoring And Alerting
- Health Check Endpoints
- Metrics Collection
- Log Aggregation
- Alert Thresholds

## Performance Considerations

### Memory Management
- Efficient Data Structures
- Garbage Collection Optimization
- Memory Pooling For Connections
- Streaming For Large Files

### CPU Optimization
- Asynchronous I/O Operations
- Multi-Threading For CPU-Intensive Tasks
- Algorithm Optimization
- Caching Strategies

### Network Efficiency
- Connection Reuse
- Bandwidth Throttling
- Compression Where Appropriate
- Protocol Optimization

## Security Architecture

### Threat Model
- Network Eavesdropping
- Man-In-The-Middle Attacks
- Deep Packet Inspection
- Denial Of Service
- Data Tampering

### Security Controls
- End-To-End Encryption
- Digital Signatures
- Certificate Pinning
- Traffic Obfuscation
- Access Control

## Future Extensibility

### Plugin System
- Modular Feature Addition
- Third-Party Integration
- Custom Protocol Support
- Alternative Storage Backends

### API Design
- RESTful Interfaces
- Versioned APIs
- Backward Compatibility
- Documentation Generation

This Architecture Provides A Solid Foundation For A Secure, Scalable, And Maintainable P2P File Sharing System.