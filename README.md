# Auto Ping - ISP Network Monitoring System

Enterprise-grade network monitoring tool for ISPs managing 500+ clients across multiple POPs.

## Features

✅ **Smart POP Search** - Autocomplete suggestions as you type  
✅ Google Sheets integration with caching  
✅ Async parallel ping (50 concurrent by default)  
✅ Auto-retry on failures  
✅ Rich terminal UI with progress bars  
✅ Works on Windows 10/11 (CMD/PowerShell)  
✅ Low latency, lightweight execution  

## Quick Start

### 1. Install Python
Download Python 3.8+ from [python.org](https://www.python.org/downloads/)  
✅ Check "Add Python to PATH" during installation

### 2. Install Dependencies
Open PowerShell in the "Auto Ping" folder:
```powershell
pip install -r requirements.txt
```

### 3. Setup Google Sheets API
1. Place your `credentials.json` in the `config/` folder
2. The sheet is already configured in `config/config.yaml`

### 4. Run the System
```powershell
python main.py
```

## Usage

1. Run `python main.py`
2. **Start typing POP name** - autocomplete suggestions appear
   - Type "Baris" → suggests "Barisal Robi"
   - Use arrow keys to select
   - Press Enter to confirm
3. Wait for ping results
4. View UP/DOWN status with color indicators

## Configuration

Edit `config/config.yaml` to customize:
- `timeout_seconds`: Ping timeout (default: 2s)
- `concurrent_limit`: Parallel pings (default: 50)
- `cache_duration_seconds`: Sheet cache time (default: 300s)

## Troubleshooting

**"Permission denied" error:**
- Run PowerShell as Administrator, OR
- Set `privileged_mode: false` in config.yaml

**"Module not found" error:**
```powershell
pip install --upgrade -r requirements.txt
```

**Sheet not found:**
- Check sheet name in `config/config.yaml`
- Verify service account has access to the sheet

**Autocomplete not working:**
- Make sure `prompt_toolkit` is installed
- Try running: `pip install prompt_toolkit`

## File Structure
```
Auto Ping/
├── config/
│   ├── credentials.json          # Your Google API key
│   ├── config.yaml               # Main settings
│   └── sheet_config.yaml         # Column mapping
├── src/
│   ├── google_sheets_handler.py  # Data fetching
│   ├── ping_engine.py            # Async ping logic
│   └── display_formatter.py      # Terminal UI
├── main.py                        # Run this!
└── requirements.txt
```

## Performance

- **500 IPs**: ~10-15 seconds
- **Cache hit**: Instant sheet load
- **Memory**: <50MB
- **CPU**: Minimal (async I/O)

## Features Demo

**Autocomplete Search:**
```
🔍 Enter POP name (start typing for suggestions): Baris
   ↓ Barisal Robi
   ↓ Barisal POP
```

**Results Display:**
```
╔════════════════════════════════╗
║ 📡 Network Ping Monitor        ║
║ POP: Barisal Robi              ║
║ Total Clients: 15              ║
╚════════════════════════════════╝

┌─────────────────────────────────┐
│ No. │ Client Name    │ Status  │
├─────────────────────────────────┤
│ 1   │ Client A       │ 🟢 UP   │
│ 2   │ Client B       │ 🔴 DOWN │
└─────────────────────────────────┘

Summary: 13 UP | 2 DOWN | Time: 3.2s
```
